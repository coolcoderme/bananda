package com.bananda.uix

import android.content.Context
import android.graphics.Color
import android.util.TypedValue
import android.view.View
import com.google.android.material.button.MaterialButton

class Button(
    text: String = "",
    fontSize: Double = 16.0,
    color: String = "#3D2E00",
    backgroundColor: String? = "#F4C430",
    onPress: BanandaHandler? = null,
) : Widget() {
    var text: String = text
        set(value) {
            field = value
            (androidView as? MaterialButton)?.text = value
        }
    var fontSize: Double = fontSize
    var color: String = color
    var onPress: BanandaHandler? = onPress

    init {
        this.backgroundColor = backgroundColor
    }

    override fun createView(context: Context): View {
        val view = MaterialButton(context)
        view.text = this.text
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSize.toFloat())
        view.setTextColor(parseColor(color, 0xFF3D2E00.toInt()))
        view.cornerRadius = dp(context, 14.0).toInt()
        view.insetTop = dp(context, 4.0).toInt()
        view.insetBottom = dp(context, 4.0).toInt()
        val bg = backgroundColor ?: "#F4C430"
        view.setBackgroundColor(parseColor(bg, Color.parseColor("#F4C430")))
        view.setOnClickListener {
            onPress?.invoke(this)
            dispatch("onPress")
        }
        applyCommon(view)
        androidView = view
        return view
    }
}
