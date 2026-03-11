{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "helper.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := .Values.nameOverride | default .Chart.Name }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- (printf "%s-%s" .Release.Name $name) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "helper.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create container environment variables from configmap
*/}}
{{- define "helper.env" -}}
{{ range $key, $val := .env }}
{{ $key }}: {{ $val | quote }}
{{- end }}
{{- end }}


{{/*
Create container environment variables from secret
*/}}
{{- define "helper.secret" -}}
{{ range $key, $val := .secrets }}
{{ $key }}: {{ $val | b64enc | quote }}
{{- end }}
{{- end }}


{{/*
Define a file checksum to trigger rollout on configmap of secret change
*/}}
{{- define "helper.checksum" -}}
{{- $ := index . 0 }}
{{- $path := index . 1 }}
{{- $resourceType := include (print $.Template.BasePath $path) $ | fromYaml -}}
{{- if $resourceType -}}
checksum-{{ $resourceType.kind | lower }}-{{ $resourceType.metadata.name }}: {{ $resourceType.data | toYaml | sha256sum }}
{{- end -}}
{{- end -}}

{{/*
Worker checksum helper - generates checksums for worker ConfigMaps and Secrets
Parameters:
- $root: The root context
- $workerName: The name of the worker
*/}}
{{- define "helper.workerChecksum" -}}
{{- $ := .root }}
{{- $workerName := .workerName }}
{{- range $.Values.workers }}
{{- if eq .name $workerName }}
{{- if .extraConfigMap }}
{{- range .extraConfigMap }}
checksum-configmap-{{ printf "%s-%s" (include "helper.fullname" $) .name }}: {{ .data | toYaml | sha256sum }}
{{- end }}
{{- end }}
{{- if .extraSecret }}
{{- range .extraSecret }}
checksum-secret-{{ printf "%s-%s" (include "helper.fullname" $) .name }}: {{ .data | toYaml | sha256sum }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}


{{/*
Common labels
*/}}
{{- define "helper.commonLabels" -}}
helm.sh/chart: {{ include "helper.chart" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Generic selector labels
Parameters:
- $root: The root context
- $componentName: The name of the component for which the selector labels are being generated
*/}}
{{- define "helper.selectorLabels" -}}
{{- $root := .root | default $ -}}
{{- $componentName := .componentName | default "app" -}}
app.kubernetes.io/name: {{ printf "%s-%s" (include "helper.fullname" $root) $componentName | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/instance: {{ $root.Release.Name | trunc 63 | trimSuffix "-" }}
{{- end -}}

{{/*
Generic app labels
Parameters:
- $root: The root context
- $componentName: The name of the component for which the selector labels are being generated
*/}}
{{- define "helper.labels" -}}
{{- $root := .root -}}
{{- $componentName := .componentName | default "app" -}}
{{ include "helper.commonLabels" $root }}
{{ include "helper.selectorLabels" (dict "root" $root "componentName" $componentName) }}
{{- end -}}
