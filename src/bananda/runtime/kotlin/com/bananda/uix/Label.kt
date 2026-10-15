package com.bananda.uix

import android.content.Context
import android.graphics.Typeface
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.TextView

class Label(
    text: String = "",
    fontSize: Number = 16,
    color: String = "#1A1A1A",
    bold: Boolean = false,
    halign: String = "left",
) : Widget() {
    var text: String = text
        set(value) {
            field = value
            (androidView as? TextView)?.text = value
        }
    var fontSize: Double = fontSize.toDouble()
        set(value) {
            field = value
            (androidView as? TextView)?.setTextSize(TypedValue.COMPLEX_UNIT_SP, value.toFloat())
        }
    var color: String = color
        set(value) {
            field = value
            (androidView as? TextView)?.setTextColor(parseColor(value, 0xFF1A1A1A.toInt()))
        }
    var bold: Boolean = bold
    var halign: String = halign
    var onPress: BanandaHandler? = null

    override fun createView(context: Context): View {
        val view = TextView(context)
        view.text = text
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSize.toFloat())
        view.setTextColor(parseColor(color, 0xFF1A1A1A.toInt()))
        if (bold) {
            view.setTypeface(view.typeface, Typeface.BOLD)
        }
        view.gravity = when (halign) {
            "center" -> Gravity.CENTER
            "right" -> Gravity.END
            else -> Gravity.START
        }
        applyCommon(view)
        onPress?.let { handler ->
            view.setOnClickListener { handler(this) }
        }
        androidView = view
        return view
    }
}
