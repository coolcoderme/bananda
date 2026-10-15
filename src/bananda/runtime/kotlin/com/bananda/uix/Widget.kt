package com.bananda.uix

import android.content.Context
import android.graphics.Color
import android.util.TypedValue
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout

data class SizeHint(val x: Double?, val y: Double?)

typealias BanandaHandler = (Widget) -> Unit
typealias BanandaValueHandler = (Widget, String) -> Unit

open class Widget {
    var id: String = ""
    var width: Any = "wrap"
    var height: Any = "wrap"
    var sizeHint: SizeHint = SizeHint(1.0, 1.0)
    var opacity: Float = 1f
    var backgroundColor: String? = null
    var padding: Double = 0.0

    val children: MutableList<Widget> = mutableListOf()
    var androidView: View? = null
        protected set

    private val handlers: MutableMap<String, MutableList<BanandaHandler>> = mutableMapOf()

    fun addWidget(child: Widget): Widget {
        children.add(child)
        return child
    }

    fun removeWidget(child: Widget) {
        children.remove(child)
    }

    fun clearWidgets() {
        children.clear()
    }

    fun bind(event: String, handler: BanandaHandler) {
        handlers.getOrPut(normalizeEvent(event)) { mutableListOf() }.add(handler)
    }

    fun dispatch(event: String) {
        handlers[normalizeEvent(event)]?.forEach { it(this) }
    }

    open fun createView(context: Context): View {
        val view = View(context)
        applyCommon(view)
        androidView = view
        return view
    }

    protected fun applyCommon(view: View) {
        view.alpha = opacity
        backgroundColor?.let {
            try {
                view.setBackgroundColor(Color.parseColor(it))
            } catch (_: IllegalArgumentException) {
                // ignore invalid colors from generated apps
            }
        }
        val pad = dp(view.context, padding).toInt()
        if (pad > 0) {
            view.setPadding(pad, pad, pad, pad)
        }
        if (id.isNotEmpty()) {
            view.tag = id
        }
    }

    fun layoutParams(context: Context): ViewGroup.LayoutParams {
        val widthPx = dimension(context, width, sizeHint.x, fillIfHint = true)
        val heightPx = dimension(context, height, sizeHint.y, fillIfHint = false)
        val params = LinearLayout.LayoutParams(widthPx, heightPx)
        if (sizeHint.x != null && sizeHint.x!! > 0.0 && widthPx == ViewGroup.LayoutParams.WRAP_CONTENT) {
            params.width = 0
            params.weight = sizeHint.x!!.toFloat()
        }
        return params
    }

    private fun dimension(context: Context, spec: Any, hint: Double?, fillIfHint: Boolean): Int {
        when (spec) {
            "match", "fill" -> return ViewGroup.LayoutParams.MATCH_PARENT
            "wrap" -> {
                if (hint != null && hint >= 1.0 && fillIfHint) {
                    return ViewGroup.LayoutParams.MATCH_PARENT
                }
                if (hint == null) {
                    return ViewGroup.LayoutParams.WRAP_CONTENT
                }
                return ViewGroup.LayoutParams.WRAP_CONTENT
            }
            is Number -> return dp(context, spec.toDouble()).toInt()
        }
        return ViewGroup.LayoutParams.WRAP_CONTENT
    }

    companion object {
        fun dp(context: Context, value: Double): Float {
            return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value.toFloat(),
                context.resources.displayMetrics,
            )
        }

        fun parseColor(value: String, fallback: Int): Int {
            return try {
                Color.parseColor(value)
            } catch (_: IllegalArgumentException) {
                fallback
            }
        }

        fun normalizeEvent(event: String): String {
            return event.replace("_", "").lowercase()
        }
    }
}
