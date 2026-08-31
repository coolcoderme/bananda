package com.bananda.uix

import android.content.Context
import android.view.View
import android.widget.GridLayout as AndroidGridLayout

class GridLayout(
    cols: Int = 1,
    rows: Int = 0,
    spacing: Double = 0.0,
) : Widget() {
    var cols: Int = cols
    var rows: Int = rows
    var spacing: Double = spacing

    override fun createView(context: Context): View {
        val layout = AndroidGridLayout(context)
        layout.columnCount = cols.coerceAtLeast(1)
        if (rows > 0) {
            layout.rowCount = rows
        }
        applyCommon(layout)
        val gap = dp(context, spacing).toInt()
        children.forEachIndexed { index, child ->
            val view = child.createView(context)
            val params = AndroidGridLayout.LayoutParams()
            params.columnSpec = AndroidGridLayout.spec(index % layout.columnCount)
            params.rowSpec = AndroidGridLayout.spec(index / layout.columnCount)
            params.setMargins(gap, gap, gap, gap)
            layout.addView(view, params)
        }
        androidView = layout
        return layout
    }
}
