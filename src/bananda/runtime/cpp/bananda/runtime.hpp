#pragma once

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#ifdef BANANDA_HAS_GTK
#include <gtk/gtk.h>
#endif

namespace bananda {

inline bool headless() {
    const char* flag = std::getenv("BANANDA_HEADLESS");
    if (flag && std::string(flag) == "1") {
        return true;
    }
    const char* display = std::getenv("DISPLAY");
    return display == nullptr || std::string(display).empty();
}

inline std::string trim(const std::string& value) {
    auto start = value.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) {
        return "";
    }
    auto end = value.find_last_not_of(" \t\n\r");
    return value.substr(start, end - start + 1);
}

inline bool isBlank(const std::string& value) { return trim(value).empty(); }

inline std::string lowercase(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return value;
}

inline std::string uppercase(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

struct SizeHint {
    std::optional<double> x = 1.0;
    std::optional<double> y = 1.0;
};

struct Dim {
    enum Kind { Wrap, Match, Dp } kind = Wrap;
    double dp = 0;
    Dim() = default;
    Dim(int value) : kind(Dp), dp(static_cast<double>(value)) {}
    Dim(double value) : kind(Dp), dp(value) {}
    Dim(const char* value) { *this = Dim(std::string(value)); }
    Dim(const std::string& value) {
        if (value == "match" || value == "fill") {
            kind = Match;
        } else if (value == "wrap") {
            kind = Wrap;
        } else {
            kind = Dp;
            dp = std::strtod(value.c_str(), nullptr);
        }
    }
};

using Handler = std::function<void(class Widget*)>;
using ValueHandler = std::function<void(class Widget*, const std::string&)>;

class Widget {
public:
    std::string id;
    Dim width;
    Dim height;
    SizeHint sizeHint;
    double opacity = 1.0;
    std::string backgroundColor;
    double padding = 0;
    Widget* parent = nullptr;
    std::vector<Widget*> children;

#ifdef BANANDA_HAS_GTK
    GtkWidget* gtk = nullptr;
#endif

    virtual ~Widget() {
        for (Widget* child : children) {
            delete child;
        }
    }

    Widget* addWidget(Widget* child) {
        child->parent = this;
        children.push_back(child);
        return child;
    }

    void removeWidget(Widget* child) {
        children.erase(std::remove(children.begin(), children.end(), child), children.end());
        child->parent = nullptr;
    }

    void clearWidgets() {
        for (Widget* child : children) {
            delete child;
        }
        children.clear();
    }

    virtual std::string widgetType() const { return "Widget"; }
    virtual std::string dumpFields() const { return ""; }

    std::string dump(int indent = 0) const {
        std::ostringstream out;
        out << std::string(static_cast<std::size_t>(indent * 2), ' ') << widgetType();
        auto fields = dumpFields();
        if (!fields.empty()) {
            out << "(" << fields << ")";
        }
        for (Widget* child : children) {
            out << "\n" << child->dump(indent + 1);
        }
        return out.str();
    }

#ifdef BANANDA_HAS_GTK
    virtual GtkWidget* createGtk() {
        gtk = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
        return gtk;
    }
#endif
};

class Label : public Widget {
public:
    std::string text;
    double fontSize = 16;
    std::string color = "#1A1A1A";
    bool bold = false;
    std::string halign = "left";
    Handler onPress;

    std::string widgetType() const override { return "Label"; }
    std::string dumpFields() const override {
        return text.empty() ? "" : "text='" + text + "'";
    }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_label_new(text.c_str());
        gtk_widget_set_halign(gtk, halign == "center" ? GTK_ALIGN_CENTER : (halign == "right" ? GTK_ALIGN_END : GTK_ALIGN_START));
        return gtk;
    }
#endif
};

class Button : public Widget {
public:
    std::string text;
    double fontSize = 16;
    std::string color = "#3D2E00";
    Handler onPress;

    std::string widgetType() const override { return "Button"; }
    std::string dumpFields() const override {
        return text.empty() ? "" : "text='" + text + "'";
    }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_button_new_with_label(text.c_str());
        g_signal_connect(
            gtk,
            "clicked",
            G_CALLBACK(+[](GtkWidget*, gpointer data) {
                auto* self = static_cast<Button*>(data);
                if (self->onPress) {
                    self->onPress(self);
                }
            }),
            this);
        return gtk;
    }
#endif
};

class TextInput : public Widget {
public:
    std::string text;
    std::string hintText;
    bool multiline = false;
    double fontSize = 16;
    ValueHandler onText;

    std::string widgetType() const override { return "TextInput"; }
    std::string dumpFields() const override {
        return hintText.empty() ? "" : "hint_text='" + hintText + "'";
    }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_entry_new();
        gtk_entry_set_text(GTK_ENTRY(gtk), text.c_str());
        if (!hintText.empty()) {
            gtk_entry_set_placeholder_text(GTK_ENTRY(gtk), hintText.c_str());
        }
        g_signal_connect(
            gtk,
            "changed",
            G_CALLBACK(+[](GtkEditable* editable, gpointer data) {
                auto* self = static_cast<TextInput*>(data);
                self->text = gtk_entry_get_text(GTK_ENTRY(editable));
                if (self->onText) {
                    self->onText(self, self->text);
                }
            }),
            this);
        return gtk;
    }
#endif
};

class BoxLayout : public Widget {
public:
    std::string orientation = "vertical";
    double spacing = 0;

    std::string widgetType() const override { return "BoxLayout"; }
    std::string dumpFields() const override { return "orientation='" + orientation + "'"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_box_new(
            orientation == "horizontal" ? GTK_ORIENTATION_HORIZONTAL : GTK_ORIENTATION_VERTICAL,
            static_cast<int>(spacing));
        gtk_container_set_border_width(GTK_CONTAINER(gtk), static_cast<guint>(padding));
        for (Widget* child : children) {
            gtk_box_pack_start(GTK_BOX(gtk), child->createGtk(), TRUE, TRUE, 0);
        }
        return gtk;
    }
#endif
};

class GridLayout : public Widget {
public:
    int cols = 1;
    int rows = 0;
    double spacing = 0;

    std::string widgetType() const override { return "GridLayout"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_grid_new();
        gtk_grid_set_column_spacing(GTK_GRID(gtk), static_cast<guint>(spacing));
        gtk_grid_set_row_spacing(GTK_GRID(gtk), static_cast<guint>(spacing));
        int columnCount = cols > 0 ? cols : 1;
        for (std::size_t i = 0; i < children.size(); ++i) {
            gtk_grid_attach(
                GTK_GRID(gtk),
                children[i]->createGtk(),
                static_cast<int>(i % columnCount),
                static_cast<int>(i / columnCount),
                1,
                1);
        }
        return gtk;
    }
#endif
};

class ScrollView : public Widget {
public:
    std::string widgetType() const override { return "ScrollView"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_scrolled_window_new(nullptr, nullptr);
        if (!children.empty()) {
            gtk_container_add(GTK_CONTAINER(gtk), children[0]->createGtk());
        }
        return gtk;
    }
#endif
};

class CheckBox : public Widget {
public:
    bool active = false;
    Handler onActive;
    std::string widgetType() const override { return "CheckBox"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_check_button_new();
        gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(gtk), active);
        g_signal_connect(
            gtk,
            "toggled",
            G_CALLBACK(+[](GtkToggleButton* button, gpointer data) {
                auto* self = static_cast<CheckBox*>(data);
                self->active = gtk_toggle_button_get_active(button);
                if (self->onActive) {
                    self->onActive(self);
                }
            }),
            this);
        return gtk;
    }
#endif
};

class Switch : public Widget {
public:
    bool active = false;
    Handler onActive;
    std::string widgetType() const override { return "Switch"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_switch_new();
        gtk_switch_set_active(GTK_SWITCH(gtk), active);
        g_signal_connect(
            gtk,
            "notify::active",
            G_CALLBACK(+[](GObject* object, GParamSpec*, gpointer data) {
                auto* self = static_cast<Switch*>(data);
                self->active = gtk_switch_get_active(GTK_SWITCH(object));
                if (self->onActive) {
                    self->onActive(self);
                }
            }),
            this);
        return gtk;
    }
#endif
};

class Slider : public Widget {
public:
    double min = 0;
    double max = 100;
    double value = 0;
    Handler onValue;
    std::string widgetType() const override { return "Slider"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, min, max, 1);
        gtk_range_set_value(GTK_RANGE(gtk), value);
        g_signal_connect(
            gtk,
            "value-changed",
            G_CALLBACK(+[](GtkRange* range, gpointer data) {
                auto* self = static_cast<Slider*>(data);
                self->value = gtk_range_get_value(range);
                if (self->onValue) {
                    self->onValue(self);
                }
            }),
            this);
        return gtk;
    }
#endif
};

class ProgressBar : public Widget {
public:
    double value = 0;
    double max = 100;
    std::string widgetType() const override { return "ProgressBar"; }

#ifdef BANANDA_HAS_GTK
    GtkWidget* createGtk() override {
        gtk = gtk_progress_bar_new();
        gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(gtk), max == 0 ? 0 : value / max);
        return gtk;
    }
#endif
};

class App {
public:
    std::string title = "BanANDa";
    Widget* root = nullptr;

    virtual ~App() { delete root; }
    virtual Widget* build() = 0;
    virtual void onStart() {}
    virtual void onStop() {}
    virtual void onPause() {}
    virtual void onResume() {}

    void start() {
        root = build();
        onStart();
        if (headless()) {
            std::cout << root->dump() << std::endl;
            return;
        }
#ifdef BANANDA_HAS_GTK
        gtk_init(nullptr, nullptr);
        GtkWidget* window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
        gtk_window_set_title(GTK_WINDOW(window), title.c_str());
        gtk_window_set_default_size(GTK_WINDOW(window), 420, 720);
        gtk_container_add(GTK_CONTAINER(window), root->createGtk());
        g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), nullptr);
        gtk_widget_show_all(window);
        gtk_main();
#else
        std::cout << root->dump() << std::endl;
#endif
    }
};

}  // namespace bananda
