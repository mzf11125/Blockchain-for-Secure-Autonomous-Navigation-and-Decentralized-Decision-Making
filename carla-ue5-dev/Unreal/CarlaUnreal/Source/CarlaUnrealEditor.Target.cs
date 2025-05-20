// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;
using System;
using EpicGames.Core;

public class CarlaUnrealEditorTarget : TargetRules
{
    [CommandLine("-unity-build")]
    bool EnableUnityBuild = true;

    private static void LogFlagStatus(string name, bool value)
    {
        var state = value ? "enabled" : "disabled";
        Console.WriteLine(string.Format("{0} is {1}.", name, state));
    }

    public CarlaUnrealEditorTarget(TargetInfo Target) :
        base(Target)
    {
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        Type = TargetType.Editor;

        ExtraModuleNames.Add("CarlaUnreal");

        LogFlagStatus("Unity build", EnableUnityBuild);

        if (!EnableUnityBuild)
        {
            bUseUnityBuild =
            bForceUnityBuild =
            bUseAdaptiveUnityBuild = false;
        }
    }
}
