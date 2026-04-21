{{- define "mylearning.name" -}}
mylearning
{{- end }}

{{- define "mylearning.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "mylearning.name" .) -}}
{{- end }}