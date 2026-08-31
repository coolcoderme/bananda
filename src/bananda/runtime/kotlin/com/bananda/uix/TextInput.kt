package com.bananda.uix

import android.content.Context
import android.text.Editable
import android.text.TextWatcher
import android.util.TypedValue
import android.view.View
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout

class TextInput(
    text: String = "",
    hintText: String = "",
    multiline: Boolean = false,
    fontSize: Number = 16,
    onText: BanandaValueHandler? = null,
) : Widget() {
    var text: String = text
        set(value) {
            if (field == value) return
            field = value
            val edit = findEdit()
            if (edit != null && edit.text?.toString() != value) {
                edit.setText(value)
            }
        }
    var hintText: String = hintText
    var multiline: Boolean = multiline
    var fontSize: Double = fontSize.toDouble()
    var onText: BanandaValueHandler? = onText

    override fun createView(context: Context): View {
        val layout = TextInputLayout(context)
        layout.hint = hintText
        val edit = TextInputEditText(context)
        edit.setText(text)
        edit.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSize.toFloat())
        if (!multiline) {
            edit.maxLines = 1
            edit.isSingleLine = true
        }
        edit.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = Unit
            override fun afterTextChanged(s: Editable?) {
                val value = s?.toString() ?: ""
                if (this@TextInput.text != value) {
                    this@TextInput.text = value
                }
                onText?.invoke(this@TextInput, value)
            }
        })
        layout.addView(edit)
        applyCommon(layout)
        androidView = layout
        return layout
    }

    private fun findEdit(): TextInputEditText? {
        val layout = androidView as? TextInputLayout ?: return null
        return layout.editText as? TextInputEditText
    }
}
