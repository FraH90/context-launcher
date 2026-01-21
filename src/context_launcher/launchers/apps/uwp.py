"""UWP/MSIX application launcher for Windows Store apps."""

import os
import subprocess
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..base import BaseLauncher, LaunchResult, ExecutableNotFoundError, ConfigurationError


# Registry of known UWP apps with their AUMIDs and protocol URIs
# AUMID format: PackageFamilyName!ApplicationId
UWP_APP_REGISTRY: Dict[str, Dict[str, str]] = {
    # Microsoft Apps
    "calculator": {
        "name": "Calculator",
        "aumid": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
        "protocol": "calculator:",
    },
    "calendar": {
        "name": "Calendar",
        "aumid": "microsoft.windowscommunicationsapps_8wekyb3d8bbwe!microsoft.windowslive.calendar",
        "protocol": "outlookcal:",
    },
    "mail": {
        "name": "Mail",
        "aumid": "microsoft.windowscommunicationsapps_8wekyb3d8bbwe!microsoft.windowslive.mail",
        "protocol": "outlookmail:",
    },
    "photos": {
        "name": "Photos",
        "aumid": "Microsoft.Windows.Photos_8wekyb3d8bbwe!App",
        "protocol": "ms-photos:",
    },
    "settings": {
        "name": "Settings",
        "aumid": "windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.immersivecontrolpanel",
        "protocol": "ms-settings:",
    },
    "store": {
        "name": "Microsoft Store",
        "aumid": "Microsoft.WindowsStore_8wekyb3d8bbwe!App",
        "protocol": "ms-windows-store:",
    },
    "weather": {
        "name": "Weather",
        "aumid": "Microsoft.BingWeather_8wekyb3d8bbwe!App",
        "protocol": "bingweather:",
    },
    "maps": {
        "name": "Maps",
        "aumid": "Microsoft.WindowsMaps_8wekyb3d8bbwe!App",
        "protocol": "bingmaps:",
    },
    "alarms": {
        "name": "Alarms & Clock",
        "aumid": "Microsoft.WindowsAlarms_8wekyb3d8bbwe!App",
        "protocol": "ms-clock:",
    },
    "camera": {
        "name": "Camera",
        "aumid": "Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
        "protocol": "microsoft.windows.camera:",
    },
    "notepad": {
        "name": "Notepad",
        "aumid": "Microsoft.WindowsNotepad_8wekyb3d8bbwe!App",
        "protocol": None,  # No protocol, use AUMID
    },
    "paint": {
        "name": "Paint",
        "aumid": "Microsoft.Paint_8wekyb3d8bbwe!App",
        "protocol": "ms-paint:",
    },
    "snipping": {
        "name": "Snipping Tool",
        "aumid": "Microsoft.ScreenSketch_8wekyb3d8bbwe!App",
        "protocol": "ms-screenclip:",
    },
    "terminal": {
        "name": "Windows Terminal",
        "aumid": "Microsoft.WindowsTerminal_8wekyb3d8bbwe!App",
        "protocol": "wt:",
    },
    "xbox": {
        "name": "Xbox",
        "aumid": "Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App",
        "protocol": "xbox:",
    },
    "feedback": {
        "name": "Feedback Hub",
        "aumid": "Microsoft.WindowsFeedbackHub_8wekyb3d8bbwe!App",
        "protocol": "feedback-hub:",
    },
    "movies": {
        "name": "Movies & TV",
        "aumid": "Microsoft.ZuneVideo_8wekyb3d8bbwe!Microsoft.ZuneVideo",
        "protocol": "mswindowsvideo:",
    },
    "groove": {
        "name": "Groove Music",
        "aumid": "Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic",
        "protocol": "mswindowsmusic:",
    },
    "voicerecorder": {
        "name": "Voice Recorder",
        "aumid": "Microsoft.WindowsSoundRecorder_8wekyb3d8bbwe!App",
        "protocol": None,
    },
    "people": {
        "name": "People",
        "aumid": "Microsoft.People_8wekyb3d8bbwe!App",
        "protocol": "ms-people:",
    },
    "gethelp": {
        "name": "Get Help",
        "aumid": "Microsoft.GetHelp_8wekyb3d8bbwe!App",
        "protocol": "ms-contact-support:",
    },
    "tips": {
        "name": "Tips",
        "aumid": "Microsoft.Getstarted_8wekyb3d8bbwe!App",
        "protocol": None,
    },
    "yourphone": {
        "name": "Phone Link",
        "aumid": "Microsoft.YourPhone_8wekyb3d8bbwe!App",
        "protocol": "ms-phone:",
    },
    "whiteboard": {
        "name": "Microsoft Whiteboard",
        "aumid": "Microsoft.Whiteboard_8wekyb3d8bbwe!App",
        "protocol": "ms-whiteboard:",
    },
    "todo": {
        "name": "Microsoft To Do",
        "aumid": "Microsoft.Todos_8wekyb3d8bbwe!App",
        "protocol": "ms-todo:",
    },
    "onenote": {
        "name": "OneNote",
        "aumid": "Microsoft.Office.OneNote_8wekyb3d8bbwe!microsoft.onenoteim",
        "protocol": "onenote:",
    },
    "clipchamp": {
        "name": "Clipchamp",
        "aumid": "Clipchamp.Clipchamp_yxz26nhyzhsrt!App",
        "protocol": None,
    },
    "clock": {
        "name": "Clock",
        "aumid": "Microsoft.WindowsAlarms_8wekyb3d8bbwe!App",
        "protocol": "ms-clock:",
    },
    # Third-party apps from Microsoft Store
    "spotify": {
        "name": "Spotify",
        "aumid": "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
        "protocol": "spotify:",
    },
    "netflix": {
        "name": "Netflix",
        "aumid": "4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App",
        "protocol": "nflx:",
    },
    "whatsapp": {
        "name": "WhatsApp",
        "aumid": "5319275A.WhatsAppDesktop_cv1g1gnamgfra!WhatsAppDesktop",
        "protocol": "whatsapp:",
    },
    "telegram": {
        "name": "Telegram",
        "aumid": "TelegramMessengerLLP.TelegramDesktop_t4vj0pshhgkwm!Telegram.TelegramDesktop.Store",
        "protocol": "tg:",
    },
    "amazon": {
        "name": "Amazon",
        "aumid": "Amazon.com.Amazon_343d40qqvtj1t!App",
        "protocol": None,
    },
    "primevideo": {
        "name": "Prime Video",
        "aumid": "AmazonVideo.PrimeVideo_pwbj9vvecjh7j!App",
        "protocol": "aiv:",
    },
    "disney": {
        "name": "Disney+",
        "aumid": "Disney.37853FC22B2CE_6rarf9sa4v8jt!App",
        "protocol": None,
    },
    "tiktok": {
        "name": "TikTok",
        "aumid": "BytedancePte.Ltd.TikTok_6yccndn111vnr!TikTok",
        "protocol": None,
    },
    "facebook": {
        "name": "Facebook",
        "aumid": "Facebook.Facebook_8xx8rvfyw5nnt!App",
        "protocol": "fb:",
    },
    "instagram": {
        "name": "Instagram",
        "aumid": "Facebook.InstagramBeta_8xx8rvfyw5nnt!Instagram",
        "protocol": "instagram:",
    },
    "twitter": {
        "name": "X (Twitter)",
        "aumid": "9E2F88E3.Twitter_wgeqdkkx372wm!Twitter",
        "protocol": None,
    },
    "linkedin": {
        "name": "LinkedIn",
        "aumid": "LinkedIn.LinkedIn_dzs1s2ag0q8q8!LinkedIn",
        "protocol": None,
    },
}


def get_installed_uwp_apps() -> List[Dict[str, Any]]:
    """Get list of installed UWP/MSIX apps on the system.

    Uses PowerShell to query installed packages.

    Returns:
        List of dicts with app info (name, package_family_name, install_location)
    """
    if sys.platform != 'win32':
        return []

    try:
        # PowerShell command to get installed UWP apps
        ps_command = '''
        Get-AppxPackage | Where-Object {$_.IsFramework -eq $false} | Select-Object Name, PackageFamilyName, InstallLocation | ConvertTo-Json
        '''

        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            import json
            apps = json.loads(result.stdout)
            # Ensure it's always a list
            if isinstance(apps, dict):
                apps = [apps]
            return apps
    except Exception:
        pass

    return []


def find_uwp_app_aumid(app_name: str) -> Optional[str]:
    """Find the AUMID for a UWP app by searching installed packages.

    Args:
        app_name: Name or partial name of the app

    Returns:
        AUMID string if found, None otherwise
    """
    if sys.platform != 'win32':
        return None

    # First check our registry
    app_key = app_name.lower()
    if app_key in UWP_APP_REGISTRY:
        return UWP_APP_REGISTRY[app_key].get('aumid')

    # Try to find by searching installed apps
    try:
        ps_command = f'''
        $app = Get-AppxPackage | Where-Object {{$_.Name -like '*{app_name}*'}} | Select-Object -First 1
        if ($app) {{
            $manifest = Get-AppxPackageManifest -Package $app.PackageFullName
            $appId = $manifest.Package.Applications.Application.Id
            Write-Output "$($app.PackageFamilyName)!$appId"
        }}
        '''

        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    return None


def is_uwp_app_installed(app_name: str) -> bool:
    """Check if a UWP app is installed.

    Args:
        app_name: Name of the app (key in UWP_APP_REGISTRY or search term)

    Returns:
        True if installed
    """
    if sys.platform != 'win32':
        return False

    app_key = app_name.lower()

    # Check registry for known app
    if app_key in UWP_APP_REGISTRY:
        aumid = UWP_APP_REGISTRY[app_key].get('aumid', '')
        if aumid:
            # Extract package family name from AUMID
            pkg_family = aumid.split('!')[0]
            try:
                result = subprocess.run(
                    ['powershell', '-Command', f'Get-AppxPackage -Name "*{pkg_family.split("_")[0]}*"'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return bool(result.stdout.strip())
            except Exception:
                pass

    # Try generic search
    try:
        result = subprocess.run(
            ['powershell', '-Command', f'Get-AppxPackage | Where-Object {{$_.Name -like "*{app_name}*"}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except Exception:
        pass

    return False


def get_uwp_app_display_name(app_key: str) -> str:
    """Get display name for a UWP app.

    Args:
        app_key: App key in registry

    Returns:
        Display name
    """
    if app_key.lower() in UWP_APP_REGISTRY:
        return UWP_APP_REGISTRY[app_key.lower()].get('name', app_key.title())
    return app_key.title()


def get_available_uwp_apps() -> List[str]:
    """Get list of known UWP apps that are installed.

    Returns:
        List of app keys that are installed
    """
    available = []
    for app_key in UWP_APP_REGISTRY:
        if is_uwp_app_installed(app_key):
            available.append(app_key)
    return sorted(available)


class UWPLauncher(BaseLauncher):
    """Launcher for UWP/MSIX Windows Store applications.

    Supports launching via:
    1. Protocol URI (e.g., ms-photos:, calculator:)
    2. Application User Model ID (AUMID)
    3. Shell activation
    """

    def __init__(self, config):
        """Initialize UWP launcher.

        Args:
            config: Launch configuration with:
                - app_name: Name of app in UWP_APP_REGISTRY or custom
                - aumid: Optional explicit AUMID
                - protocol: Optional protocol URI
                - arguments: Optional arguments (for protocol URIs)
        """
        super().__init__(config)
        self.app_name = config.app_name
        self.aumid = config.parameters.get('aumid')
        self.protocol = config.parameters.get('protocol')
        self.arguments = config.parameters.get('arguments', [])

        # If no explicit AUMID/protocol, look up in registry
        app_key = self.app_name.lower()
        if app_key in UWP_APP_REGISTRY:
            if not self.aumid:
                self.aumid = UWP_APP_REGISTRY[app_key].get('aumid')
            if not self.protocol:
                self.protocol = UWP_APP_REGISTRY[app_key].get('protocol')

    def launch(self) -> LaunchResult:
        """Launch the UWP application.

        Returns:
            LaunchResult with launch status
        """
        if sys.platform != 'win32':
            return LaunchResult.error_result("UWP apps are only supported on Windows")

        try:
            # Method 1: Try protocol URI first (most reliable for user-facing launch)
            if self.protocol:
                return self._launch_via_protocol()

            # Method 2: Try AUMID via shell activation
            if self.aumid:
                return self._launch_via_aumid()

            # Method 3: Try to find AUMID by searching
            found_aumid = find_uwp_app_aumid(self.app_name)
            if found_aumid:
                self.aumid = found_aumid
                return self._launch_via_aumid()

            return LaunchResult.error_result(
                f"Could not find UWP app '{self.app_name}'. "
                "Provide an AUMID or protocol URI."
            )

        except Exception as e:
            self._log_error(f"UWP launch failed: {e}", e)
            return LaunchResult.error_result(f"Launch failed: {e}", e)

    def _launch_via_protocol(self) -> LaunchResult:
        """Launch app via protocol URI.

        Returns:
            LaunchResult
        """
        protocol = self.protocol

        # Append arguments to protocol if any
        if self.arguments:
            if isinstance(self.arguments, list):
                args_str = ' '.join(self.arguments)
            else:
                args_str = str(self.arguments)
            protocol = f"{protocol}{args_str}"

        self._log_launch(f"Launching UWP app via protocol: {protocol}")

        # Use explorer.exe to open protocol URI
        process = subprocess.Popen(
            ['explorer.exe', protocol],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        app_display = get_uwp_app_display_name(self.app_name)
        return LaunchResult.success_result(
            f"Successfully launched {app_display}",
            process.pid
        )

    def _launch_via_aumid(self) -> LaunchResult:
        """Launch app via AUMID using shell activation.

        Returns:
            LaunchResult
        """
        self._log_launch(f"Launching UWP app via AUMID: {self.aumid}")

        # Use PowerShell to activate the app via its AUMID
        ps_command = f'''
        $shell = New-Object -ComObject Shell.Application
        $shell.ShellExecute("shell:AppsFolder\\{self.aumid}")
        '''

        process = subprocess.Popen(
            ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        app_display = get_uwp_app_display_name(self.app_name)
        return LaunchResult.success_result(
            f"Successfully launched {app_display}",
            process.pid
        )

    def validate_config(self) -> bool:
        """Validate launch configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If invalid
        """
        if sys.platform != 'win32':
            raise ConfigurationError("UWP apps are only supported on Windows")

        # Check if we have protocol, AUMID, or can find the app
        if self.protocol or self.aumid:
            return True

        # Try to find in registry
        app_key = self.app_name.lower()
        if app_key in UWP_APP_REGISTRY:
            return True

        # Try to find by searching
        if find_uwp_app_aumid(self.app_name):
            return True

        raise ExecutableNotFoundError(
            f"UWP app '{self.app_name}' not found. "
            "Either install it from Microsoft Store or provide an explicit AUMID."
        )

    def get_executable_path(self) -> str:
        """Get executable path (returns AUMID for UWP apps).

        Returns:
            AUMID or protocol string
        """
        if self.aumid:
            return f"shell:AppsFolder\\{self.aumid}"
        if self.protocol:
            return self.protocol
        return ""
