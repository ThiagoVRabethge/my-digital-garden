package com.mydigitalgarden.app

import android.content.Intent
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import java.io.File

class MainActivity : FlutterActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        processShareIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        processShareIntent(intent)
    }

    /**
     * Extrai o texto/URL compartilhado e salva em flet_shared.txt
     * no diretório interno do app, onde o Python pode ler.
     */
    private fun processShareIntent(intent: Intent) {
        if (intent.action != Intent.ACTION_SEND) return
        if (intent.type?.startsWith("text/") != true) return

        val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
            ?.trim()
            ?.takeIf { it.isNotEmpty() }
            ?: return

        try {
            // filesDir = /data/user/0/<package>/files/
            // Acessível pelo processo Python dentro do mesmo app
            File(filesDir, "flet_shared.txt").writeText(sharedText)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}