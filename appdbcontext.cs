using Microsoft.EntityFrameworkCore;
using System;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> opts) : base(opts) { }
    public DbSet<Report> Reports { get; set; }
}

public class Report
{
    public int Id { get; set; }
    public string AgentId { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public string Branch { get; set; } = string.Empty;
    public string BuildOk { get; set; } = string.Empty;
    public string Committed { get; set; } = string.Empty;
    public string CommitSha { get; set; } = string.Empty;
    public string PayloadJson { get; set; } = string.Empty;
}