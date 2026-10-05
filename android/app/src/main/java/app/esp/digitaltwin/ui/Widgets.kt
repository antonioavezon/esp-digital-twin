package app.esp.digitaltwin.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import app.esp.digitaltwin.R
import app.esp.digitaltwin.engine.HzIssue
import androidx.compose.ui.res.stringResource

@Composable
fun Panel(title: String, modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp), content = {
            Text(title, style = MaterialTheme.typography.titleMedium)
            content()
        })
    }
}

@Composable
fun UnitMenu(value: String, options: List<String>, modifier: Modifier = Modifier, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Column(modifier) {
        OutlinedButton(
            onClick = { open = true },
            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
        ) { Text(value, maxLines = 1) }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            options.forEach { option ->
                DropdownMenuItem(text = { Text(option) }, onClick = { onPick(option); open = false })
            }
        }
    }
}

@Composable
fun ChoiceField(label: String, value: String, options: List<String>, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth()) {
        Text(label, style = MaterialTheme.typography.labelLarge)
        OutlinedButton(
            onClick = { open = true },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).semantics { contentDescription = label },
        ) {
            Text(value.ifBlank { "—" }, maxLines = 2)
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option) },
                    onClick = {
                        onPick(option)
                        open = false
                    },
                )
            }
        }
    }
}

@Composable
fun NumberField(label: String, value: String, hint: String? = null, onValue: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onValue,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(label) },
        supportingText = hint?.let { { Text(it) } },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
    )
}

@Composable
fun FrequencyCard(session: SessionViewModel) {
    Column(Modifier.fillMaxWidth()) {
        NumberField("Hz", session.hzDraft) { session.editHz(it) }
        val issue = session.hzIssue
        if (issue != null) {
            Text(
                if (issue == HzIssue.EMPTY) "Falta frecuencia" else "30 a 90",
                color = MaterialTheme.colorScheme.error,
            )
        }
        TextButton(onClick = session::resetHz, modifier = Modifier.heightIn(min = 48.dp)) {
            Text("60 Hz")
        }
    }
}

@Composable
fun InlineError(text: String?) {
    if (!text.isNullOrBlank()) {
        Text(text, color = MaterialTheme.colorScheme.error)
    }
}

@Composable
fun ActionRow(content: @Composable () -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        content()
    }
}

@Composable
fun PrimaryAction(label: String, onClick: () -> Unit) {
    Button(onClick = onClick, modifier = Modifier.heightIn(min = 48.dp)) { Text(label) }
}
