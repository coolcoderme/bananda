package com.bananda.uix

import android.content.Context
import android.view.View
import android.widget.LinearLayout
import android.widget.Space

class BoxLayout(
    orientation: String = "vertical",
    spacing: Number = 0,
    padding: Number = 0,
    sizeHint: SizeHint = SizeHint(1.0, 1.0),
    height: Any = "wrap",
    width: Any = "wrap",
) : Widget() {
    var orientation: String = orientation
    var spacing: Double = spacing.toDouble()

    init {
        this.padding = padding.toDouble()
        this.sizeHint = sizeHint
        this.height = height
        this.width = width
    }

    override fun createView(context: Context): View {
        val layout = LinearLayout(context)
        layout.orientation = if (orientation == "horizontal") {
            LinearLayout.HORIZONTAL
        } else {
            LinearLayout.VERTICAL
        }
        val pad = dp(context, padding).toInt()
        layout.setPadding(pad, pad, pad, pad)
        applyCommon(layout)
        children.forEachIndexed { index, child ->
            layout.addView(child.createView(context), child.layoutParams(context))
            if (spacing > 0 && index < children.lastIndex) {
                val space = Space(context)
                val gap = dp(context, spacing).toInt()
                val spaceParams = if (layout.orientation == LinearLayout.VERTICAL) {
                    LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, gap)
                } else {
                    LinearLayout.LayoutParams(gap, LinearLayout.LayoutParams.MATCH_PARENT)
                }
                layout.addView(space, spaceParams)
            }
        }
        androidView = layout
        return layout
    }
}
