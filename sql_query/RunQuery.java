import com.microsoft.aad.msal4j.*;

import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.PosixFilePermissions;
import java.sql.*;
import java.util.*;

/**
 * Azure SQL query runner used by the `run-query` Python CLI.
 *
 * Authentication uses Azure Active Directory via MSAL4J with the Microsoft SQL
 * JDBC driver's own registered public-client ID, so the token is accepted by
 * the same servers DataGrip's "ActiveDirectoryInteractive" reaches. The token
 * (and its refresh token) is cached on disk at ~/.azuresql/token-cache.json so
 * subsequent runs authenticate silently with no browser window.
 *
 *   - authMode "silent":      use the cached token / silent refresh only. If no
 *                             usable credential is cached, exit 3 (no browser).
 *   - authMode "interactive": open the browser to sign in and refresh the cache.
 *
 * If the query argument is empty, the program only authenticates (used by
 * `run-query --login`) and does not connect.
 *
 * The result set is written straight to the output CSV; the row data never
 * crosses back to the Python process.
 *
 * Run as a single-file source program (Java 11+):
 *   java -cp "<driver+msal jars>" RunQuery.java \
 *       <server> <port> <db> <user> <tenant> <authMode> <outCsv> <query>
 *
 * Prints the row count to stdout. Progress/diagnostics go to stderr.
 * Exit codes: 0 ok, 2 usage, 3 not authenticated (silent mode, no cache).
 */
public class RunQuery {

    // The Microsoft SQL JDBC driver's public-client app id (extracted from
    // mssql-jdbc). Tokens from this client are accepted by Azure SQL where a
    // generic Azure CLI token is rejected.
    static final String CLIENT_ID = "7f98cb04-cd1e-40df-9140-3bf7e2cea4db";
    // The double slash is intentional: it yields a token whose audience is
    // "https://database.windows.net/" (WITH the trailing slash), which is the
    // SPN Azure SQL expects. A single-slash ".default" scope produces audience
    // "https://database.windows.net" (no slash), which the server rejects with
    // "server is not currently configured to accept this token".
    static final Set<String> SCOPES =
            Collections.singleton("https://database.windows.net//.default");
    static final String REDIRECT_URI = "http://localhost";

    public static void main(String[] args) throws Exception {
        if (args.length != 8) {
            System.err.println("usage: RunQuery <server> <port> <db> <user> "
                    + "<tenant> <authMode> <outCsv> <query>");
            System.exit(2);
        }
        String server   = args[0];
        String port      = args[1];
        String db         = args[2];
        String user       = args[3];
        String tenant     = args[4];
        String authMode   = args[5];
        String outCsv     = args[6];
        String query      = args[7];

        String token = acquireToken(user, tenant, authMode);

        if (query.isEmpty()) {
            System.err.println("Authenticated. Credentials cached for future runs.");
            return;
        }

        String url = "jdbc:sqlserver://" + server + ":" + port
                + ";databaseName=" + db
                + ";encrypt=true"
                + ";trustServerCertificate=false"
                + ";applicationIntent=ReadOnly";

        Properties props = new Properties();
        props.setProperty("accessToken", token);

        try (Connection conn = DriverManager.getConnection(url, props)) {
            conn.setReadOnly(true);
            try (Statement st = conn.createStatement();
                 ResultSet rs = st.executeQuery(query);
                 Writer w = new BufferedWriter(
                         new OutputStreamWriter(new FileOutputStream(outCsv), StandardCharsets.UTF_8))) {
                ResultSetMetaData md = rs.getMetaData();
                int n = md.getColumnCount();
                String[] header = new String[n];
                for (int i = 1; i <= n; i++) header[i - 1] = md.getColumnLabel(i);
                writeRow(w, header);

                long rows = 0;
                while (rs.next()) {
                    String[] vals = new String[n];
                    for (int i = 1; i <= n; i++) {
                        Object o = rs.getObject(i);
                        vals[i - 1] = (o == null) ? "" : o.toString();
                    }
                    writeRow(w, vals);
                    rows++;
                }
                w.flush();
                System.err.println("Wrote " + rows + " row(s) to " + outCsv);
                System.out.println(rows);
            }
        }
    }

    /** Acquire an Azure SQL access token, silently if possible. */
    static String acquireToken(String user, String tenant, String authMode) throws Exception {
        String authority = "https://login.microsoftonline.com/"
                + (tenant.isEmpty() ? "organizations" : tenant);
        Path cacheFile = Paths.get(System.getProperty("user.home"), ".azuresql", "token-cache.json");

        PublicClientApplication app = PublicClientApplication.builder(CLIENT_ID)
                .authority(authority)
                .setTokenCacheAccessAspect(new FileTokenCache(cacheFile))
                .build();

        // Try silent acquisition from the on-disk cache first (no browser).
        try {
            Set<IAccount> accounts = app.getAccounts().join();
            IAccount account = pickAccount(accounts, user);
            if (account != null) {
                IAuthenticationResult r = app.acquireTokenSilently(
                        SilentParameters.builder(SCOPES, account).build()).join();
                if (r != null && r.accessToken() != null) {
                    System.err.println("Authenticated from cached credentials.");
                    return r.accessToken();
                }
            }
        } catch (Exception e) {
            // Fall through to interactive (or fail) below.
        }

        if (!"interactive".equals(authMode)) {
            System.err.println("Not authenticated (no valid cached credentials). "
                    + "Run `run-query --login` to sign in.");
            System.exit(3);
        }

        System.err.println("Opening browser for Azure AD sign-in...");
        InteractiveRequestParameters.InteractiveRequestParametersBuilder b =
                InteractiveRequestParameters.builder(new URI(REDIRECT_URI)).scopes(SCOPES);
        if (!user.isEmpty()) b.loginHint(user);
        IAuthenticationResult r = app.acquireToken(b.build()).join();
        return r.accessToken();
    }

    static IAccount pickAccount(Set<IAccount> accounts, String user) {
        if (accounts == null || accounts.isEmpty()) return null;
        if (!user.isEmpty()) {
            for (IAccount a : accounts) {
                if (user.equalsIgnoreCase(a.username())) return a;
            }
        }
        return accounts.iterator().next();
    }

    /** MSAL token cache backed by a 0600 file in the user's home directory. */
    static class FileTokenCache implements ITokenCacheAccessAspect {
        private final Path file;
        FileTokenCache(Path file) { this.file = file; }

        @Override
        public void beforeCacheAccess(ITokenCacheAccessContext ctx) {
            try {
                if (Files.exists(file)) {
                    ctx.tokenCache().deserialize(
                            new String(Files.readAllBytes(file), StandardCharsets.UTF_8));
                }
            } catch (Exception e) {
                System.err.println("warn: could not read token cache: " + e.getMessage());
            }
        }

        @Override
        public void afterCacheAccess(ITokenCacheAccessContext ctx) {
            try {
                if (ctx.hasCacheChanged()) {
                    Files.createDirectories(file.getParent());
                    Files.write(file,
                            ctx.tokenCache().serialize().getBytes(StandardCharsets.UTF_8));
                    try {
                        Files.setPosixFilePermissions(file,
                                PosixFilePermissions.fromString("rw-------"));
                    } catch (UnsupportedOperationException ignore) {
                        // Non-POSIX filesystem; skip.
                    }
                }
            } catch (Exception e) {
                System.err.println("warn: could not write token cache: " + e.getMessage());
            }
        }
    }

    static void writeRow(Writer w, String[] cells) throws IOException {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < cells.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(csv(cells[i]));
        }
        sb.append("\r\n");
        w.write(sb.toString());
    }

    static String csv(String s) {
        if (s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }
}
