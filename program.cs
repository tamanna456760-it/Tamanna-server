using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(options =>
{
    options.Limits.MaxRequestBodySize = 1_048_576;
});

var connectionString =
    builder.Configuration.GetValue<string>("Database:ConnectionString")
    ?? "Data Source=data/reports.db";
var sqlite = new SqliteConnectionStringBuilder(connectionString);
if (!string.IsNullOrWhiteSpace(sqlite.DataSource) && sqlite.DataSource != ":memory:")
{
    var dbPath = Path.GetFullPath(sqlite.DataSource);
    Directory.CreateDirectory(Path.GetDirectoryName(dbPath)!);
    sqlite.DataSource = dbPath;
    connectionString = sqlite.ToString();
}

builder.Services.AddDbContext<AppDbContext>(options => options.UseSqlite(connectionString));
var app = builder.Build();

app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["X-Frame-Options"] = "DENY";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    context.Response.Headers["Cache-Control"] = "no-store";
    await next();
});

bool IsAuthorized(HttpRequest request, IConfiguration configuration)
{
    var expected = configuration["Orchestrator:Token"];
    if (string.IsNullOrWhiteSpace(expected))
        return false;

    var authorization = request.Headers.Authorization.ToString();
    if (!authorization.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        return false;

    var supplied = authorization["Bearer ".Length..].Trim();
    if (supplied.Length == 0)
        return false;

    return CryptographicOperations.FixedTimeEquals(
        Encoding.UTF8.GetBytes(supplied),
        Encoding.UTF8.GetBytes(expected));
}

app.MapGet("/health", () => Results.Ok(new
{
    status = "ok",
    service = "tamanna-dotnet-orchestrator"
}));

app.MapGet("/health/ready", async (AppDbContext db) =>
{
    try
    {
        return await db.Database.CanConnectAsync()
            ? Results.Ok(new { status = "ready", database = "ok" })
            : Results.Json(new { status = "not_ready" }, statusCode: 503);
    }
    catch (Exception)
    {
        return Results.Json(new { status = "not_ready" }, statusCode: 503);
    }
});

app.MapPost("/api/report", async (HttpRequest request, AppDbContext db, IConfiguration cfg, ILogger<Program> logger) =>
{
    if (string.IsNullOrWhiteSpace(cfg["Orchestrator:Token"]))
        return Results.Json(new { error = "server authentication is not configured" }, statusCode: 503);

    if (!IsAuthorized(request, cfg))
        return Results.Unauthorized();

    if (!request.HasJsonContentType())
        return Results.Json(new { error = "Content-Type must be application/json" }, statusCode: 415);

    ReportPayload? payload;
    try
    {
        payload = await JsonSerializer.DeserializeAsync<ReportPayload>(request.Body);
    }
    catch (JsonException)
    {
        return Results.BadRequest(new { error = "invalid JSON" });
    }

    if (payload is null || string.IsNullOrWhiteSpace(payload.AgentId) || payload.AgentId.Length > 128)
        return Results.BadRequest(new { error = "agentId must be a non-empty string of at most 128 characters" });
    if ((payload.Branch?.Length ?? 0) > 128 || (payload.CommitSha?.Length ?? 0) > 64)
        return Results.BadRequest(new { error = "branch or commitSha exceeds the allowed length" });

    var report = new Report
    {
        AgentId = payload.AgentId.Trim(),
        Timestamp = DateTime.UtcNow,
        Branch = payload.Branch ?? "",
        BuildOk = payload.BuildOk ? "true" : "false",
        Committed = payload.Committed ? "true" : "false",
        CommitSha = payload.CommitSha ?? "",
        PayloadJson = JsonSerializer.Serialize(payload)
    };

    try
    {
        db.Reports.Add(report);
        await db.SaveChangesAsync();
        return Results.Created($"/api/report/{report.Id}", new { status = "ok", id = report.Id });
    }
    catch (Exception exception)
    {
        logger.LogError(exception, "Could not persist orchestrator report");
        return Results.Json(new { error = "database operation failed" }, statusCode: 500);
    }
});

app.MapGet("/api/reports", async (HttpRequest request, AppDbContext db, IConfiguration cfg) =>
{
    if (string.IsNullOrWhiteSpace(cfg["Orchestrator:Token"]))
        return Results.Json(new { error = "server authentication is not configured" }, statusCode: 503);
    if (!IsAuthorized(request, cfg))
        return Results.Unauthorized();

    var reports = await db.Reports
        .AsNoTracking()
        .OrderByDescending(report => report.Id)
        .Take(200)
        .Select(report => new
        {
            report.Id,
            report.AgentId,
            report.Timestamp,
            report.Branch,
            report.BuildOk,
            report.Committed,
            report.CommitSha
        })
        .ToListAsync();

    return Results.Ok(reports);
});

app.MapGet("/", () => Results.Ok(new
{
    service = "Tamanna .NET Orchestrator",
    status = "running",
    health = "/health",
    readiness = "/health/ready"
}));

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.EnsureCreatedAsync();
}

app.Run();

public class ReportPayload
{
    public string? AgentId { get; set; }
    public string? Branch { get; set; }
    public bool BuildOk { get; set; }
    public bool Committed { get; set; }
    public string? CommitSha { get; set; }
    public JsonElement? FixerOut { get; set; }
    public JsonElement? BuildOut { get; set; }
    public bool HasChanges { get; set; }
    public string? RepoPath { get; set; }
}
