import os
import sys
import shutil
import argparse
import uuid
import pefile

VCXPROJ_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" ToolsVersion="17.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
    <ProjectConfiguration Include="Debug|{PLATFORM}">
      <Configuration>Debug</Configuration>
      <Platform>{PLATFORM}</Platform>
    </ProjectConfiguration>
    <ProjectConfiguration Include="Release|{PLATFORM}">
      <Configuration>Release</Configuration>
      <Platform>{PLATFORM}</Platform>
    </ProjectConfiguration>
  </ItemGroup>
  <PropertyGroup Label="Globals">
    <VCProjectVersion>17.0</VCProjectVersion>
    <ProjectGuid>{{{GUID}}}</ProjectGuid>
    <RootNamespace>{PROXY_NAME}</RootNamespace>
    <WindowsTargetPlatformVersion>10.0</WindowsTargetPlatformVersion>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />
  <PropertyGroup Label="Configuration">
    <ConfigurationType>DynamicLibrary</ConfigurationType>
    <PlatformToolset>v143</PlatformToolset>
    <CharacterSet>MultiByte</CharacterSet>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.props" />
  <PropertyGroup>
    <TargetName>{PROXY_NAME}</TargetName>
    <OutDir>$(SolutionDir)bin\\$(Platform)\\$(Configuration)\\</OutDir>
  </PropertyGroup>
  <ItemDefinitionGroup>
    <ClCompile>
      <WarningLevel>Level3</WarningLevel>
      <PreprocessorDefinitions>WIN32_LEAN_AND_MEAN;%(PreprocessorDefinitions)</PreprocessorDefinitions>
      <RuntimeLibrary>MultiThreaded</RuntimeLibrary>
    </ClCompile>
    <Link>
      <ModuleDefinitionFile>{DEF_NAME}</ModuleDefinitionFile>
      <SubSystem>Windows</SubSystem>
      <AdditionalDependencies>{SDK_LIB};%(AdditionalDependencies)</AdditionalDependencies>
    </Link>
  </ItemDefinitionGroup>
  <ItemGroup>
    <ClCompile Include="{CPP_NAME}" />
  </ItemGroup>
  <ItemGroup>
    <None Include="{DEF_NAME}" />
  </ItemGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />
</Project>
"""

SLN_TEMPLATE = """Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") = "{PROXY_NAME}", "{VCXPROJ_NAME}", "{{{GUID}}}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|{PLATFORM} = Debug|{PLATFORM}
		Release|{PLATFORM} = Release|{PLATFORM}
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{{{GUID}}}.Debug|{PLATFORM}.ActiveCfg = Debug|{PLATFORM}
		{{{GUID}}}.Debug|{PLATFORM}.Build.0 = Debug|{PLATFORM}
		{{{GUID}}}.Release|{PLATFORM}.ActiveCfg = Release|{PLATFORM}
		{{{GUID}}}.Release|{PLATFORM}.Build.0 = Release|{PLATFORM}
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
"""

CPP_TEMPLATE = """#include <windows.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved)
{
    switch (reason)
    {
    case DLL_PROCESS_ATTACH:
        break;
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
"""

def parse_args():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("dll_path")
    p.add_argument("-n", "--name", default="expfunc.dll")
    p.add_argument("-s", "--arch", choices=["x86", "x64"], default="x86")
    return p.parse_args()

def gen_proxy_project(script_dir, proxy_name, def_name, arch):
    platform = "Win32" if arch == "x86" else "x64"
    proj_guid = str(uuid.uuid4()).upper()
    cpp_name = f"{proxy_name}.cpp"
    vcxproj_name = f"{proxy_name}.vcxproj"
    sln_name = f"{proxy_name}.sln"
    sdk_lib = f"{proxy_name.lower()}.lib"

    with open(os.path.join(script_dir, cpp_name), "w", encoding="utf-8") as f:
        f.write(CPP_TEMPLATE)

    vcxproj = VCXPROJ_TEMPLATE.format(
        PLATFORM=platform,
        GUID=proj_guid,
        PROXY_NAME=proxy_name,
        CPP_NAME=cpp_name,
        DEF_NAME=def_name,
        SDK_LIB=sdk_lib,
    )
    with open(os.path.join(script_dir, vcxproj_name), "w", encoding="utf-8") as f:
        f.write(vcxproj)

    sln = SLN_TEMPLATE.format(
        PROXY_NAME=proxy_name,
        VCXPROJ_NAME=vcxproj_name,
        GUID=proj_guid,
        PLATFORM=platform,
    )
    with open(os.path.join(script_dir, sln_name), "w", encoding="utf-8") as f:
        f.write(sln)

    print(f"Projeto gerado: {cpp_name}, {vcxproj_name}, {sln_name}")
    print(f"AdditionalDependencies: {sdk_lib} (SDK import lib, requerida p/ o linker MSVC resolver os forwarders do .def)")

def generate_def(dll_path, out_name, arch):
    if not os.path.isfile(dll_path):
        print(f"Erro: DLL não encontrada: {dll_path}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    dst_path = os.path.join(script_dir, out_name)
    shutil.copy2(dll_path, dst_path)

    pe = pefile.PE(dst_path)
    if not hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        print("Erro: A DLL não possui tabela de exportações.")
        sys.exit(1)

    real_name = os.path.splitext(out_name)[0]                     
    proxy_name = os.path.splitext(os.path.basename(dll_path))[0]    
    def_name = f"{proxy_name}.def"
    def_path = os.path.join(script_dir, def_name)

    def is_data_export(rva):
        for sec in pe.sections:
            start = sec.VirtualAddress
            end = start + sec.Misc_VirtualSize
            if start <= rva < end:
                return not bool(sec.Characteristics & 0x20000000)
        return False

    with open(def_path, "w", encoding="utf-8") as f:
        f.write(f"LIBRARY {proxy_name}\n\n")
        f.write("EXPORTS\n")
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            data_flag = " DATA" if is_data_export(exp.address) else ""
            if exp.name:
                name = exp.name.decode("utf-8")
                f.write(f"    {name}={real_name}.{name}{data_flag}\n")
            else:
                ordinal = exp.ordinal
                f.write(f"    @{ordinal}={real_name}.#{ordinal} NONAME{data_flag}\n")

    pe.close()
    print(f"DLL copiada para: {dst_path}")
    print(f"Arquivo gerado: {def_path}")

    gen_proxy_project(script_dir, proxy_name, def_name, arch)

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('    AutoGenDef.py <caminho_da_dll> [-n nome_saida.dll] [-s x86|x64]')
        sys.exit(1)
    args = parse_args()
    generate_def(args.dll_path, args.name, args.arch)

if __name__ == "__main__":
    main()
