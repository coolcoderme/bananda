using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Bananda
{
    public delegate void BanandaHandler(Widget instance);
    public delegate void BanandaValueHandler(Widget instance, string value);

    public readonly struct SizeHint
    {
        public readonly double? X;
        public readonly double? Y;
        public SizeHint(double? x, double? y) { X = x; Y = y; }
    }

    public class Widget
    {
        public string Id { get; set; } = "";
        public object Width { get; set; } = "wrap";
        public object Height { get; set; } = "wrap";
        public SizeHint SizeHint { get; set; } = new SizeHint(1, 1);
        public double Opacity { get; set; } = 1;
        public string? BackgroundColor { get; set; }
        public double Padding { get; set; }
        public List<Widget> Children { get; } = new List<Widget>();

        public Widget AddWidget(Widget child)
        {
            Children.Add(child);
            return child;
        }

        public void RemoveWidget(Widget child) => Children.Remove(child);
        public void ClearWidgets() => Children.Clear();

        public virtual string WidgetType => GetType().Name;
        public virtual string DumpFields() => "";

        public string Dump(int indent = 0)
        {
            var pad = new string(' ', indent * 2);
            var extra = DumpFields();
            var header = string.IsNullOrEmpty(extra) ? WidgetType : $"{WidgetType}({extra})";
            var sb = new StringBuilder();
            sb.Append(pad).Append(header);
            foreach (var child in Children)
            {
                sb.Append('\n').Append(child.Dump(indent + 1));
            }
            return sb.ToString();
        }
    }

    public class Label : Widget
    {
        public string Text { get; set; } = "";
        public double FontSize { get; set; } = 16;
        public string Color { get; set; } = "#1A1A1A";
        public bool Bold { get; set; }
        public string Halign { get; set; } = "left";
        public BanandaHandler? OnPress { get; set; }
        public override string DumpFields() => string.IsNullOrEmpty(Text) ? "" : $"text='{Text}'";
    }

    public class Button : Widget
    {
        public string Text { get; set; } = "";
        public double FontSize { get; set; } = 16;
        public string Color { get; set; } = "#3D2E00";
        public BanandaHandler? OnPress { get; set; }
        public override string DumpFields() => string.IsNullOrEmpty(Text) ? "" : $"text='{Text}'";
    }

    public class TextInput : Widget
    {
        public string Text { get; set; } = "";
        public string HintText { get; set; } = "";
        public bool Multiline { get; set; }
        public double FontSize { get; set; } = 16;
        public BanandaValueHandler? OnText { get; set; }
        public override string DumpFields() => string.IsNullOrEmpty(HintText) ? "" : $"hint_text='{HintText}'";
    }

    public class BoxLayout : Widget
    {
        public string Orientation { get; set; } = "vertical";
        public double Spacing { get; set; }
        public override string DumpFields() => $"orientation='{Orientation}'";
    }

    public class GridLayout : Widget
    {
        public int Cols { get; set; } = 1;
        public int Rows { get; set; }
        public double Spacing { get; set; }
    }

    public class ScrollView : Widget { }

    public class CheckBox : Widget
    {
        public bool Active { get; set; }
        public BanandaHandler? OnActive { get; set; }
    }

    public class Switch : Widget
    {
        public bool Active { get; set; }
        public BanandaHandler? OnActive { get; set; }
    }

    public class Slider : Widget
    {
        public double Min { get; set; }
        public double Max { get; set; } = 100;
        public double Value { get; set; }
        public BanandaHandler? OnValue { get; set; }
    }

    public class ProgressBar : Widget
    {
        public double Value { get; set; }
        public double Max { get; set; } = 100;
    }

    public abstract class App
    {
        public virtual string Title { get; set; } = "BanANDa";
        public Widget? Root { get; private set; }

        public abstract Widget Build();
        public virtual void OnStart() { }
        public virtual void OnStop() { }
        public virtual void OnPause() { }
        public virtual void OnResume() { }

        public void Start()
        {
            Root = Build();
            OnStart();
#if WINDOWS
            if (!IsHeadless())
            {
                WinFormsHost.Show(this, Root);
                return;
            }
#endif
            Console.WriteLine(Root.Dump());
        }

        public static bool IsHeadless()
        {
            return Environment.GetEnvironmentVariable("BANANDA_HEADLESS") == "1"
                || string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DISPLAY"));
        }
    }
}
