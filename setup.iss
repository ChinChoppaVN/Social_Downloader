[Setup]
AppName=Social Media Downloader
AppVersion=2.0
DefaultDirName={autopf}\Social Media Downloader
DefaultGroupName=Social Media Downloader
UninstallDisplayIcon={app}\Social Media Downloader.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=SocialMediaDownloader_Setup
SetupIconFile=assets\CH.ico
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[InstallDelete]
; Xóa thư mục assets cũ nếu có từ các phiên bản cài đặt trước để tránh xung đột đường dẫn
Type: filesandordirs; Name: "{app}\assets"

[Files]
; Thêm tất cả file từ thư mục dist vào thư mục cài đặt (bao gồm exe, _internal, assets, yt-dlp, ffmpeg, theme)
Source: "dist\Social Media Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Tạo shortcut trong Start Menu
Name: "{group}\Social Media Downloader"; Filename: "{app}\Social Media Downloader.exe"
; Tạo shortcut trên Desktop
Name: "{autodesktop}\Social Media Downloader"; Filename: "{app}\Social Media Downloader.exe"

[Run]
; Tùy chọn chạy ứng dụng sau khi cài đặt
Filename: "{app}\Social Media Downloader.exe"; Description: "Khởi chạy Social Media Downloader"; Flags: nowait postinstall skipifsilent
