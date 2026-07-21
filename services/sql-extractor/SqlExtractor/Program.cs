using Microsoft.SqlServer.TransactSql.ScriptDom;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapPost("/extract", async (HttpContext context) =>
{
    using var reader = new StreamReader(context.Request.Body);
    var rawSql = await reader.ReadToEndAsync();

    if (string.IsNullOrWhiteSpace(rawSql))
    {
        return Results.BadRequest(new { error = "Empty SQL input" });
    }

    var parser = new TSql160Parser(initialQuotedIdentifiers: true);
    IList<ParseError> errors;
    var fragment = parser.Parse(new StringReader(rawSql), out errors);

    var extractor = new DmlQueryExtractor();
    fragment.Accept(extractor);

    var result = new
    {
        query_count = extractor.Queries.Count,
        parse_errors = errors.Select(e => new
        {
            line = e.Line,
            column = e.Column,
            message = e.Message,
        }).ToList(),
        queries = extractor.Queries.Select(q => new
        {
            type = q.Type,
            start_line = q.StartLine,
            sql = q.Sql,
        }).ToList(),
    };

    return Results.Ok(result);
});

app.MapGet("/health", () => Results.Ok(new { status = "ok", parser = "ScriptDom TSql160" }));

app.Run();

public class DmlQueryExtractor : TSqlFragmentVisitor
{
    public List<ExtractedQuery> Queries { get; } = new();

    public override void Visit(SelectStatement node)
    {
        AddQuery(node, "SELECT");
    }

    public override void Visit(InsertStatement node)
    {
        // Keep INSERT...SELECT (has business logic)
        // The InsertSpecification contains the source
        if (node.InsertSpecification?.InsertSource is SelectInsertSource)
        {
            AddQuery(node, "INSERT_SELECT");
        }
    }

    private void AddQuery(TSqlFragment node, string type)
    {
        var sql = GetFragmentText(node);
        if (!string.IsNullOrWhiteSpace(sql))
        {
            Queries.Add(new ExtractedQuery
            {
                Type = type,
                Sql = sql,
                StartLine = node.StartLine,
                StartColumn = node.StartColumn,
            });
        }
    }

    private string GetFragmentText(TSqlFragment fragment)
    {
        if (fragment.ScriptTokenStream == null) return "";

        var tokens = fragment.ScriptTokenStream;
        var start = fragment.FirstTokenIndex;
        var end = fragment.LastTokenIndex;

        if (start < 0 || end < 0 || start >= tokens.Count) return "";

        var sb = new System.Text.StringBuilder();
        for (int i = start; i <= end && i < tokens.Count; i++)
        {
            sb.Append(tokens[i].Text);
        }
        return sb.ToString();
    }
}

public class ExtractedQuery
{
    public string Type { get; set; } = "";
    public string Sql { get; set; } = "";
    public int StartLine { get; set; }
    public int StartColumn { get; set; }
}
