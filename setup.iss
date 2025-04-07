[Setup]
AppName=Social Media Downloader
AppVersion=1.0
DefaultDirName={autopf}\Social Media Downloader
DefaultGroupName=Social Media Downloader
UninstallDisplayIcon={app}\Social Media Downloader.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=SocialMediaDownloader_Setup

[Files]
; Thêm tất cả file từ thư mục dist vào thư mục cài đặt
Source: "dist\Social Media Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Tạo shortcut trong Start Menu
Name: "{group}\Social Media Downloader"; Filename: "{app}\Social Media Downloader.exe"
; Tạo shortcut trên Desktop
Name: "{commondesktop}\Social Media Downloader"; Filename: "{app}\Social Media Downloader.exe"

[Run]
; Tùy chọn chạy ứng dụng sau khi cài đặt
Filename: "{app}\Social Media Downloader.exe"; Description: "Chạy ứng dụng"; Flags: nowait postinstall skipifsilent