using System.Globalization;
using System.Xml.Linq;

if (args.Length == 0)
{
    PrintUsage();
    return 1;
}

try
{
    var options = Options.Parse(args);
    ConvertBmFontToXnaTxt(options);
    Console.WriteLine($"Generated: {options.OutputPath}");
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine($"Conversion failed: {ex.Message}");
    return 1;
}

static void ConvertBmFontToXnaTxt(Options options)
{
    var document = XDocument.Load(options.InputPath, LoadOptions.None);
    var commonElement = document.Root?.Element("common")
        ?? throw new InvalidOperationException("Missing common element in FNT.");
    var charsElement = document.Root?.Element("chars")
        ?? throw new InvalidOperationException("Missing chars element in FNT.");
    var charElements = charsElement.Elements("char").ToList();

    var pageCount = ParseByte(commonElement.Attribute("pages"), "common.pages");
    var lineHeight = options.LineHeightOverride != 0
        ? options.LineHeightOverride
        : ParseInt(commonElement.Attribute("lineHeight"), "common.lineHeight");
    var declaredCharCount = ParseInt(charsElement.Attribute("count"), "chars.count");

    using var output = new FileStream(options.OutputPath, FileMode.Create, FileAccess.Write, FileShare.None);
    using var writer = new BinaryWriter(output);

    writer.Write(pageCount);
    writer.Write(declaredCharCount);

    foreach (var charElement in charElements)
    {
        WriteGlyphRecord(writer, charElement, options.AsciiExtraSpacing, options.CharacterSpacingCompensation);
    }

    writer.Write(lineHeight);
    writer.Write(0);
    writer.Write((byte)1);
    writer.Write((byte)42);
    writer.Write((byte)0);
}

static void WriteGlyphRecord(BinaryWriter writer, XElement charElement, float asciiExtraSpacing, float characterSpacingCompensation)
{
    var id = ParseInt(charElement.Attribute("id"), "char.id");
    var x = ParseInt(charElement.Attribute("x"), "char.x");
    var y = ParseInt(charElement.Attribute("y"), "char.y");
    var width = ParseInt(charElement.Attribute("width"), "char.width");
    var height = ParseInt(charElement.Attribute("height"), "char.height");
    var xOffset = ParseFloat(charElement.Attribute("xoffset"), "char.xoffset");
    var yOffset = ParseInt(charElement.Attribute("yoffset"), "char.yoffset");
    var xAdvance = ParseInt(charElement.Attribute("xadvance"), "char.xadvance");
    var page = ParseByte(charElement.Attribute("page"), "char.page");

    xAdvance = (int)(xAdvance + characterSpacingCompensation);

    if (id >= 33 && id <= 127)
    {
        xAdvance = (int)(xAdvance + (2f * asciiExtraSpacing));
        xOffset += asciiExtraSpacing;
    }

    writer.Write(x);
    writer.Write(y);
    writer.Write(width);
    writer.Write(height);
    writer.Write(0);
    writer.Write(yOffset);
    writer.Write(xAdvance);
    writer.Write(0);
    writer.Write((ushort)id);
    writer.Write(xOffset);
    writer.Write((float)width);
    writer.Write(((float)(xAdvance - width)) - xOffset);
    writer.Write(page);
}

static int ParseInt(XAttribute? attribute, string name)
{
    if (attribute is null)
    {
        throw new InvalidOperationException($"Missing attribute: {name}");
    }

    return int.Parse(attribute.Value, CultureInfo.InvariantCulture);
}

static float ParseFloat(XAttribute? attribute, string name)
{
    if (attribute is null)
    {
        throw new InvalidOperationException($"Missing attribute: {name}");
    }

    return float.Parse(attribute.Value, CultureInfo.InvariantCulture);
}

static byte ParseByte(XAttribute? attribute, string name)
{
    if (attribute is null)
    {
        throw new InvalidOperationException($"Missing attribute: {name}");
    }

    return byte.Parse(attribute.Value, CultureInfo.InvariantCulture);
}

static void PrintUsage()
{
    Console.WriteLine("Usage:");
    Console.WriteLine("  XnaFontRebuilder <input.fnt> [output.txt] [lineHeightOverride] [asciiExtraSpacing] [characterSpacingCompensation]");
    Console.WriteLine("  XnaFontRebuilder <input.fnt> [output.txt] --line-height <value> --latin-compensation <value> --character-spacing-compensation <value>");
}

internal sealed record Options(string InputPath, string OutputPath, int LineHeightOverride, float AsciiExtraSpacing, float CharacterSpacingCompensation)
{
    public static Options Parse(string[] args)
    {
        var inputPath = Path.GetFullPath(args[0]);
        if (!File.Exists(inputPath))
        {
            throw new FileNotFoundException("Input FNT file not found.", inputPath);
        }

        var outputPath = Path.Combine(
            Path.GetDirectoryName(inputPath) ?? Environment.CurrentDirectory,
            $"{Path.GetFileNameWithoutExtension(inputPath)}.txt");

        var lineHeightOverride = 30;
        var asciiExtraSpacing = 0.5f;
        var characterSpacingCompensation = 0f;

        var remaining = args.Skip(1).ToList();
        if (remaining.Count > 0 && !remaining[0].StartsWith("-", StringComparison.Ordinal))
        {
            outputPath = Path.GetFullPath(remaining[0]);
            remaining.RemoveAt(0);
        }

        if (remaining.Count > 0 && !remaining[0].StartsWith("-", StringComparison.Ordinal))
        {
            lineHeightOverride = int.Parse(remaining[0], CultureInfo.InvariantCulture);
            remaining.RemoveAt(0);
        }

        if (remaining.Count > 0 && !remaining[0].StartsWith("-", StringComparison.Ordinal))
        {
            asciiExtraSpacing = float.Parse(remaining[0], CultureInfo.InvariantCulture);
            remaining.RemoveAt(0);
        }

        if (remaining.Count > 0 && !remaining[0].StartsWith("-", StringComparison.Ordinal))
        {
            characterSpacingCompensation = float.Parse(remaining[0], CultureInfo.InvariantCulture);
            remaining.RemoveAt(0);
        }

        for (var i = 0; i < remaining.Count; i++)
        {
            var current = remaining[i];
            switch (current)
            {
                case "--line-height":
                case "--lineHeight":
                    if (i + 1 >= remaining.Count)
                    {
                        throw new ArgumentException("--line-height requires a value.");
                    }

                    lineHeightOverride = int.Parse(remaining[++i], CultureInfo.InvariantCulture);
                    break;
                case "--latin-compensation":
                case "--latinCompensation":
                case "--ascii-extra-spacing":
                    if (i + 1 >= remaining.Count)
                    {
                        throw new ArgumentException("--latin-compensation requires a value.");
                    }

                    asciiExtraSpacing = float.Parse(remaining[++i], CultureInfo.InvariantCulture);
                    break;
                case "--character-spacing-compensation":
                case "--characterSpacingCompensation":
                case "--char-spacing":
                    if (i + 1 >= remaining.Count)
                    {
                        throw new ArgumentException("--character-spacing-compensation requires a value.");
                    }

                    characterSpacingCompensation = float.Parse(remaining[++i], CultureInfo.InvariantCulture);
                    break;
                default:
                    throw new ArgumentException($"Unknown argument: {current}");
            }
        }

        return new Options(inputPath, outputPath, lineHeightOverride, asciiExtraSpacing, characterSpacingCompensation);
    }
}
