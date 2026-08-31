#if WINDOWS
using System.Drawing;
using System.Windows.Forms;

namespace Bananda
{
    internal static class WinFormsHost
    {
        public static void Show(App app, Widget root)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            var form = new Form
            {
                Text = app.Title,
                Width = 420,
                Height = 720,
                BackColor = Color.FromArgb(255, 248, 225),
            };
            form.Controls.Add(Build(root));
            Application.Run(form);
        }

        private static Control Build(Widget widget)
        {
            switch (widget)
            {
                case BoxLayout box:
                    var panel = new FlowLayoutPanel
                    {
                        Dock = DockStyle.Fill,
                        FlowDirection = box.Orientation == "horizontal" ? FlowDirection.LeftToRight : FlowDirection.TopDown,
                        AutoScroll = true,
                        Padding = new Padding((int)box.Padding),
                        WrapContents = false,
                    };
                    foreach (var child in box.Children)
                    {
                        panel.Controls.Add(Build(child));
                    }
                    return panel;
                case Label label:
                    return new System.Windows.Forms.Label
                    {
                        Text = label.Text,
                        AutoSize = true,
                        Font = new Font("Segoe UI", (float)label.FontSize, label.Bold ? FontStyle.Bold : FontStyle.Regular),
                    };
                case Button button:
                    var btn = new System.Windows.Forms.Button
                    {
                        Text = button.Text,
                        AutoSize = true,
                        BackColor = Color.FromArgb(244, 196, 48),
                    };
                    btn.Click += (_, _) => button.OnPress?.Invoke(button);
                    return btn;
                case TextInput input:
                    var boxEdit = new TextBox { Text = input.Text, Width = 280 };
                    boxEdit.TextChanged += (_, _) =>
                    {
                        input.Text = boxEdit.Text;
                        input.OnText?.Invoke(input, boxEdit.Text);
                    };
                    return boxEdit;
                case CheckBox check:
                    var cb = new System.Windows.Forms.CheckBox { Checked = check.Active };
                    cb.CheckedChanged += (_, _) =>
                    {
                        check.Active = cb.Checked;
                        check.OnActive?.Invoke(check);
                    };
                    return cb;
                case Slider slider:
                    var bar = new TrackBar
                    {
                        Minimum = (int)slider.Min,
                        Maximum = (int)slider.Max,
                        Value = (int)slider.Value,
                        Width = 280,
                    };
                    bar.ValueChanged += (_, _) =>
                    {
                        slider.Value = bar.Value;
                        slider.OnValue?.Invoke(slider);
                    };
                    return bar;
                default:
                    var fallback = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown };
                    foreach (var child in widget.Children)
                    {
                        fallback.Controls.Add(Build(child));
                    }
                    return fallback;
            }
        }
    }
}
#endif
