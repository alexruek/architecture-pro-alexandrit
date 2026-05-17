// SerilogSetup.cs
// Конфигурация Serilog для MES API (C#/ASP.NET Core).
//
// NuGet-пакеты (добавить в .csproj):
// <PackageReference Include="Serilog.AspNetCore" Version="8.0.0" />
// <PackageReference Include="Serilog.Formatting.Compact" Version="2.0.0" />
// <PackageReference Include="Serilog.Enrichers.Environment" Version="2.3.0" />
// <PackageReference Include="Serilog.Enrichers.Thread" Version="3.1.0" />

using Serilog;
using Serilog.Formatting.Compact;

namespace Alexandrite.MES.Api;

public static class SerilogSetup
{
    public static WebApplicationBuilder ConfigureLogging(this WebApplicationBuilder builder)
    {
        var environment = builder.Environment.EnvironmentName;

        var loggerConfig = new LoggerConfiguration()
            // Обогащение каждой записи
            .Enrich.FromLogContext()
            .Enrich.WithEnvironmentName()
            .Enrich.WithThreadId()
            .Enrich.WithProperty("service", "mes-api")
            .Enrich.WithProperty("env", environment.ToLower());

        if (builder.Environment.IsDevelopment())
        {
            // В dev: читаемый вывод
            loggerConfig.WriteTo.Console();
            loggerConfig.MinimumLevel.Debug();
        }
        else
        {
            // В prod/release: JSON в stdout, подхватывается Promtail
            loggerConfig.WriteTo.Console(new CompactJsonFormatter());
            loggerConfig.MinimumLevel.Information();
        }

        Log.Logger = loggerConfig.CreateLogger();

        builder.Host.UseSerilog();

        return builder;
    }
}

// Пример использования в Program.cs:
//
// var builder = WebApplication.CreateBuilder(args);
// builder.ConfigureLogging();
// ...
// app.UseSerilogRequestLogging(options =>
// {
//     options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
//     {
//         diagnosticContext.Set("user_id", httpContext.User?.FindFirst("sub")?.Value ?? "anonymous");
//     };
// });

// Пример логирования бизнес-события в сервисе:
//
// public class OrderService
// {
//     private readonly ILogger<OrderService> _logger;
//
//     public async Task UpdateOrderStatus(string orderId, string oldStatus, string newStatus, string changedBy)
//     {
//         using (LogContext.PushProperty("order_id", orderId))
//         {
//             _logger.LogInformation(
//                 "Order status changed: {OldStatus} -> {NewStatus} by {ChangedBy}",
//                 oldStatus, newStatus, changedBy
//             );
//         }
//     }
//
//     public async Task StartPriceCalculation(string orderId, int polygonCount)
//     {
//         using (LogContext.PushProperty("order_id", orderId))
//         {
//             _logger.LogInformation(
//                 "Price calculation started. PolygonCount={PolygonCount}",
//                 polygonCount
//             );
//         }
//     }
// }
