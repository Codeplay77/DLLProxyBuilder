# DLLProxyBuilder

Gera automaticamente um projeto de DLL proxy (forwarder) para Visual Studio 2022 a partir de uma DLL alvo, extraindo suas exportações via `pefile` e criando um `.def` com forwarders.

## O que faz

1. Copia a DLL alvo com um novo nome (a "real" DLL, ex: `expfunc.dll`).
2. Lê a tabela de exportações (`DIRECTORY_ENTRY_EXPORT`) e gera um `.def` com forwarders (`func=real_dll.func`), preservando exports nomeados, ordinais (`NONAME`) e marcando exports de dados (`DATA`).
3. Gera um stub `.cpp` com `DllMain` mínimo.
4. Gera `.vcxproj` + `.sln` (toolset v143, `DynamicLibrary`, WarningLevel3, RuntimeLibrary estático) já configurados com `ModuleDefinitionFile` apontando pro `.def`.

O binário final da proxy exporta as mesmas funções da DLL original, forwardando chamadas para a cópia renomeada — útil para hooking/interceptação via DLL proxying (ex: `version.dll`, `d3d9.dll`, etc).

## Uso

```
python dll_proxy_generator.py <caminho_da_dll> [-n nome_saida.dll] [-s x86|x64]
```

| Argumento | Descrição | Default |
|---|---|---|
| `dll_path` | Caminho da DLL alvo (obrigatório) | — |
| `-n`, `--name` | Nome de saída da cópia da DLL real | `expfunc.dll` |
| `-s`, `--arch` | Arquitetura do projeto gerado | `x86` |

### Exemplo

```
python dll_proxy_generator.py C:\Games\App\version.dll -n version_real.dll -s x86
```

Gera na pasta do script:
- `version_real.dll` (cópia da DLL original)
- `version.def` (forwarders)
- `version.cpp` (stub DllMain)
- `version.vcxproj` / `version.sln`

O `RootNamespace`/`TargetName` do projeto usa o nome base da DLL original (sem extensão) — o binário compilado deve ser renomeado para o nome da DLL que você quer sequestrar (ex: `version.dll`) e colocado ao lado do executável alvo, junto com a cópia renomeada da DLL real.

## Requisitos

- Python 3 + [`pefile`](https://pypi.org/project/pefile/)
- Visual Studio 2022 (toolset v143) para compilar o projeto gerado

## Observações

- `AdditionalDependencies` no `.vcxproj` referencia `<nome>.lib` — se a DLL alvo não tiver import lib disponível, remova/ajuste essa entrada manualmente (não é necessária para o link de uma DLL de forwarders puros).
- Exports sem nome (apenas ordinal) são forwardados via `@ordinal=real.#ordinal NONAME`.
- Detecção de export de dados é feita checando a característica `IMAGE_SCN_MEM_EXECUTE` (0x20000000) da seção onde a RVA do export cai.

## Licença

MIT License

Copyright (c) 2026 Codeplay77

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
