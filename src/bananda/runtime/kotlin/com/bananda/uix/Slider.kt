package com.bananda.uix

import android.content.Context
import android.view.View
import android.widget.SeekBar

class Slider(
    min: Double = 0.0,
    max: Double = 100.0,
    value: Double = 0.0,
    onValue: BanandaHandler? = null,
) : Widget() {
    var min: Double = min
    var max: Double = max
    var value: Double = value
        set(newValue) {
            field = newValue
            (androidView as? SeekBar)?.progress = toProgress(newValue)
        }
    var onValue: BanandaHandler? = onValue

    override fun createView(context: Context): View {
        val view = SeekBar(context)
        view.max = 1000
        view.progress = toProgress(value)
        view.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                value = min + (max - min) * (progress / 1000.0)
                onValue?.invoke(this@Slider)
                dispatch("onValue")
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) = Unit
            override fun onStopTrackingTouch(seekBar: SeekBar?) = Unit
        })
        applyCommon(view)
        androidView = view
        return view
    }

    private fun toProgress(raw: Double): Int {
        val span = (max - min).takeIf { it != 0.0 } ?: 1.0
        return (((raw - min) / span) * 1000.0).toInt().coerceIn(0, 1000)
    }
}
