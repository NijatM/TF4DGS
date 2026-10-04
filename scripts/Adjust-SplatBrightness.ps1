<#
Create a separate, brighter standard 3DGS PLY while preserving every non-color
attribute and vertex order. Gain acts on Gaussian RGB before display clipping.
It is not a physical relighting model or an exposure change to source images.
#>
param(
    [Parameter(Mandatory=$true)][string]$InputPly,
    [Parameter(Mandatory=$true)][string]$OutputPly,
    [ValidateRange(0.01,16.0)][double]$Gain = 1.4
)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $InputPly).Path
$destinationPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPly)
if ($sourcePath.Equals($destinationPath,[System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose a separate output file; the source must remain unchanged.'
}
if (Test-Path -LiteralPath $destinationPath) { throw 'The output file already exists; choose a new name.' }
if (-not ('TF4DGSSplatBrightness' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;

public static class TF4DGSSplatBrightness {
    private sealed class Layout {
        public byte[] Header;
        public long Count;
        public List<string> Properties = new List<string>();
        public int[] Colors;
        public int[] DcColors;
        public int[] RestColors;
        public int[] NonColors;
        public int Stride { get { return Properties.Count * 4; } }
    }
    public sealed class Result {
        public long Gaussians;
        public double RgbGain;
        public int ColorProperties;
        public bool AllNonColorBytesIdentical;
        public string NonColorSha256;
        public string Source;
        public string Output;
    }
    private static Layout ReadLayout(FileStream stream) {
        var header = new List<byte>();
        var lineBytes = new List<byte>();
        var lines = new List<string>();
        while (header.Count < 65536) {
            int b = stream.ReadByte();
            if (b < 0) throw new InvalidDataException("Missing PLY header");
            header.Add((byte)b);
            if (b == 10) {
                string line = Encoding.ASCII.GetString(lineBytes.ToArray()).TrimEnd('\r');
                lines.Add(line);
                lineBytes.Clear();
                if (line == "end_header") break;
            } else lineBytes.Add((byte)b);
        }
        if (lines.Count == 0 || lines[0] != "ply" || lines[lines.Count-1] != "end_header" ||
            !lines.Contains("format binary_little_endian 1.0"))
            throw new InvalidDataException("Expected a binary little-endian Gaussian PLY");
        var layout = new Layout { Header=header.ToArray() };
        bool vertices = false;
        foreach (string line in lines) {
            string[] parts = line.Split(new char[] {' '}, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length == 0) continue;
            if (parts[0] == "element") {
                if (parts.Length != 3 || parts[1] != "vertex" || vertices)
                    throw new InvalidDataException("Only one vertex element is supported");
                layout.Count = long.Parse(parts[2],System.Globalization.CultureInfo.InvariantCulture);
                vertices = true;
            } else if (parts[0] == "property") {
                if (!vertices || parts.Length != 3 || (parts[1] != "float" && parts[1] != "float32"))
                    throw new InvalidDataException("Expected scalar float Gaussian properties");
                layout.Properties.Add(parts[2]);
            }
        }
        if (!vertices || layout.Count <= 0 || layout.Properties.Count == 0 ||
            layout.Properties.Distinct().Count() != layout.Properties.Count)
            throw new InvalidDataException("Invalid Gaussian vertex layout");
        foreach (string required in new string[] {"x","y","z","opacity","scale_0","scale_1","scale_2","rot_0","rot_1","rot_2","rot_3","f_dc_0","f_dc_1","f_dc_2"})
            if (!layout.Properties.Contains(required)) throw new InvalidDataException("Missing property: " + required);
        layout.Colors = Enumerable.Range(0,layout.Properties.Count)
            .Where(i => layout.Properties[i].StartsWith("f_dc_") || layout.Properties[i].StartsWith("f_rest_")).ToArray();
        layout.DcColors = layout.Colors.Where(i => layout.Properties[i].StartsWith("f_dc_")).ToArray();
        layout.RestColors = layout.Colors.Where(i => layout.Properties[i].StartsWith("f_rest_")).ToArray();
        layout.NonColors = Enumerable.Range(0,layout.Properties.Count).Except(layout.Colors).ToArray();
        long expected = checked(layout.Count * layout.Stride);
        if (stream.Length - stream.Position != expected)
            throw new InvalidDataException("PLY payload size differs from its vertex layout");
        return layout;
    }
    private static void ReadFully(Stream stream,byte[] bytes,int count) {
        int offset=0;
        while (offset<count) {
            int read=stream.Read(bytes,offset,count-offset);
            if (read==0) throw new EndOfStreamException();
            offset+=read;
        }
    }
    private static string HashNonColors(string path) {
        using (var input=File.OpenRead(path)) {
            Layout layout=ReadLayout(input);
            var bytes=new byte[4096*layout.Stride];
            var geometry=new byte[4096*layout.NonColors.Length*4];
            using (var sha=SHA256.Create()) {
                long remaining=layout.Count;
                while (remaining>0) {
                    int count=(int)Math.Min(4096,remaining);
                    ReadFully(input,bytes,count*layout.Stride);
                    int packed=0;
                    for (int row=0;row<count;row++) {
                        foreach (int index in layout.NonColors) {
                            Buffer.BlockCopy(bytes,row*layout.Stride+index*4,geometry,packed,4);
                            packed+=4;
                        }
                    }
                    sha.TransformBlock(geometry,0,packed,geometry,0);
                    remaining-=count;
                }
                sha.TransformFinalBlock(new byte[0],0,0);
                return BitConverter.ToString(sha.Hash).Replace("-","").ToLowerInvariant();
            }
        }
    }
    public static Result Adjust(string source,string output,double gain) {
        if (!BitConverter.IsLittleEndian) throw new PlatformNotSupportedException("Little-endian host required");
        string partial=output+".partial";
        Layout layout;
        using (var input=File.OpenRead(source)) {
            layout=ReadLayout(input);
            using (var destination=new FileStream(partial,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
                destination.Write(layout.Header,0,layout.Header.Length);
                var bytes=new byte[4096*layout.Stride];
                var floats=new float[4096*layout.Properties.Count];
                long remaining=layout.Count;
                // Standard 3DGS RGB = C0*f_dc + higher-order SH + 0.5.
                const double C0=0.28209479177387814;
                double dcOffset=(gain-1.0)*0.5/C0;
                while (remaining>0) {
                    int count=(int)Math.Min(4096,remaining);
                    int byteCount=count*layout.Stride;
                    ReadFully(input,bytes,byteCount);
                    Buffer.BlockCopy(bytes,0,floats,0,byteCount);
                    for (int row=0;row<count;row++) {
                        int start=row*layout.Properties.Count;
                        foreach (int index in layout.DcColors)
                            floats[start+index]=(float)(gain*floats[start+index]+dcOffset);
                        foreach (int index in layout.RestColors)
                            floats[start+index]=(float)(gain*floats[start+index]);
                    }
                    Buffer.BlockCopy(floats,0,bytes,0,byteCount);
                    destination.Write(bytes,0,byteCount);
                    remaining-=count;
                }
                destination.Flush(true);
            }
        }
        string sourceHash=HashNonColors(source);
        string outputHash=HashNonColors(partial);
        if (sourceHash!=outputHash) throw new InvalidDataException("Non-color attributes changed; output not published");
        File.Move(partial,output);
        return new Result { Gaussians=layout.Count, RgbGain=gain, ColorProperties=layout.Colors.Length,
            AllNonColorBytesIdentical=true, NonColorSha256=sourceHash, Source=source, Output=output };
    }
}
'@
}
[TF4DGSSplatBrightness]::Adjust($sourcePath,$destinationPath,$Gain) | ConvertTo-Json
