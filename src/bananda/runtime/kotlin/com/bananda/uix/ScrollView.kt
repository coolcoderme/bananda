package com.bananda.uix

import android.content.Context
import android.view.View
import android.widget.ScrollView as AndroidScrollView

class ScrollView : Widget() {
    override fun createView(context: Context): View {
        val scroll = AndroidScrollView(context)
        applyCommon(scroll)
        children.firstOrNull()?.let { child ->
            scroll.addView(child.createView(context), child.layoutParams(context))
        }
        androidView = scroll
        return scroll
    }
}
