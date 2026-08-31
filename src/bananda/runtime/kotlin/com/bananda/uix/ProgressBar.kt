package com.bananda.uix

import android.content.Context
import android.view.View
import android.widget.ProgressBar as AndroidProgressBar

class ProgressBar(
    value: Double = 0.0,
    max: Double = 100.0,
) : Widget() {
    var value: Double = value
        set(newValue) {
            field = newValue
            (androidView as? AndroidProgressBar)?.progress = newValue.toInt()
        }
    var max: Double = max

    override fun createView(context: Context): View {
        val view = AndroidProgressBar(context, null, android.R.attr.progressBarStyleHorizontal)
        view.max = max.toInt().coerceAtLeast(1)
        view.progress = value.toInt()
        applyCommon(view)
        androidView = view
        return view
    }
}
