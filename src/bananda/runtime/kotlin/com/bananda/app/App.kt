package com.bananda.app

import android.app.Activity
import android.view.View
import com.bananda.uix.Widget

abstract class App {
    lateinit var activity: Activity
    open var title: String = "BanANDa"
    var root: Widget? = null
        private set

    fun attach(activity: Activity) {
        this.activity = activity
        activity.title = title
        onStart()
    }

    abstract fun build(): Widget

    open fun onStart() {}
    open fun onStop() {}
    open fun onPause() {}
    open fun onResume() {}

    fun createContentView(): View {
        val tree = build()
        root = tree
        return tree.createView(activity)
    }
}
