package com.bananda.uix

import android.content.Context
import android.view.View
import androidx.appcompat.widget.SwitchCompat

class Switch(
    active: Boolean = false,
    onActive: BanandaHandler? = null,
) : Widget() {
    var active: Boolean = active
        set(value) {
            field = value
            (androidView as? SwitchCompat)?.isChecked = value
        }
    var onActive: BanandaHandler? = onActive

    override fun createView(context: Context): View {
        val view = SwitchCompat(context)
        view.isChecked = active
        view.setOnCheckedChangeListener { _, isChecked ->
            active = isChecked
            onActive?.invoke(this)
            dispatch("onActive")
        }
        applyCommon(view)
        androidView = view
        return view
    }
}
