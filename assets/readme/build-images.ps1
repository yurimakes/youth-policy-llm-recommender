param([string]$Repository = (Join-Path $PSScriptRoot '../..'))
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
function Color([string]$hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }
function Brush([string]$hex) { [System.Drawing.SolidBrush]::new((Color $hex)) }
function RoundPath([float]$x,[float]$y,[float]$w,[float]$h,[float]$radius) {
    $p = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $d = $radius * 2
    $p.AddArc($x,$y,$d,$d,180,90)
    $p.AddArc($x+$w-$d,$y,$d,$d,270,90)
    $p.AddArc($x+$w-$d,$y+$h-$d,$d,$d,0,90)
    $p.AddArc($x,$y+$h-$d,$d,$d,90,90)
    $p.CloseFigure()
    return $p
}
function Round($g,[float]$x,[float]$y,[float]$w,[float]$h,[float]$radius,[string]$fill,[string]$stroke='') {
    $p = RoundPath $x $y $w $h $radius
    $b = Brush $fill
    $g.FillPath($b,$p); $b.Dispose()
    if($stroke) { $pen=[System.Drawing.Pen]::new((Color $stroke),1); $g.DrawPath($pen,$p); $pen.Dispose() }
    $p.Dispose()
}
function Text($g,[string]$value,[float]$x,[float]$y,[float]$size,[string]$hex,[bool]$bold=$false,[float]$width=1500,[float]$height=150,[bool]$center=$false) {
    $style = if($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    $font = [System.Drawing.Font]::new('Malgun Gothic',$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    $b = Brush $hex
    $format = [System.Drawing.StringFormat]::new()
    $format.FormatFlags = [System.Drawing.StringFormatFlags]::NoWrap
    if($center) { $format.Alignment = [System.Drawing.StringAlignment]::Center }
    $g.DrawString($value,$font,$b,[System.Drawing.RectangleF]::new($x,$y,$width,$height),$format)
    $format.Dispose(); $font.Dispose(); $b.Dispose()
}
function Canvas([int]$height) {
    $bitmap = [System.Drawing.Bitmap]::new(1600,$height,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bitmap)
    $g.Clear([System.Drawing.Color]::White)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    return @{Image=$bitmap; G=$g}
}
$destination = Join-Path $Repository 'assets/readme'
$cover = Canvas 680
$g = $cover.G
$clip = RoundPath 0 0 1600 680 36
$g.SetClip($clip)
$gradient = [System.Drawing.Drawing2D.LinearGradientBrush]::new([System.Drawing.Rectangle]::new(0,0,1600,680),(Color '#f7faff'),(Color '#e7f0ff'),0)
$g.FillRectangle($gradient,0,0,1600,680); $gradient.Dispose()
$orb = Brush '#dce9ff'; $g.FillEllipse($orb,1108,-165,620,620); $orb.Dispose()
$orb = Brush '#e5ecff'; $g.FillEllipse($orb,988,206,450,450); $orb.Dispose()
$icon = [System.Drawing.Image]::FromFile((Join-Path $Repository 'demo/app-icon-192.png'))
$g.DrawImage($icon,[System.Drawing.Rectangle]::new(76,66,56,56)); $icon.Dispose()
Text $g '지원장바구니' 150 59 36 '#14243b' $true
Text $g '청년정책 탐색 · 준비 도우미' 150 105 21 '#68809d' $false
Text $g '나에게 맞는 지원,' 72 194 66 '#14243b' $true
Text $g '찾기부터 준비까지.' 72 277 66 '#14243b' $true
Text $g '정책 이름을 몰라도 괜찮아요.' 75 385 27 '#55708d'
Text $g '일상 카드에서 시작해 다음 행동을 함께 정리해요.' 75 432 27 '#55708d'
$illustration = [System.Drawing.Image]::FromFile((Join-Path $destination 'basket-illustration.png'))
$g.DrawImage($illustration,[System.Drawing.Rectangle]::new(885,-46,660,603)); $illustration.Dispose()
$steps = @('내 상황으로 시작','필요한 지원 담기','준비 · 상담으로 연결')
for($i=0;$i -lt 3;$i++) {
    $x=76+$i*493
    Round $g $x 550 454 80 18 '#ffffff' '#dee8f7'
    Text $g ('0'+($i+1)) ($x+25) 570 22 '#3182f6' $true
    Text $g $steps[$i] ($x+84) 569 26 '#294867' $true
    if($i -lt 2) { Text $g '→' ($x+463) 569 27 '#93aac9' }
}
$g.ResetClip(); $clip.Dispose(); $g.Dispose()
$cover.Image.Save((Join-Path $destination 'cover.png'),[System.Drawing.Imaging.ImageFormat]::Png); $cover.Image.Dispose()
$journey = Canvas 1050
$g = $journey.G
Round $g 0 0 1600 1050 36 '#f7f9fc'
Text $g 'HOW IT WORKS' 48 48 22 '#3182f6' $true
Text $g '시작부터 준비까지, 한 흐름으로' 46 83 42 '#14243b' $true
$titles = @('일상 카드로 시작','관심 있는 지원 담기','준비할 일 정리','상담으로 이어가기')
$intros = @(@('길게 설명하지 않아도,','지금 상황 하나부터.'),@('지원 후보를 살펴보고,','원하는 항목을 담아요.'),@('신청기간 · 서류 · 남은 조건을','하나씩 확인해요.'),@('내가 답한 정보와','기관에 물어볼 것을 모아요.'))
$files = @('01-situation.png','04-directions.png','08-preparation.png','09-consultation.png')
$captions = @('모르거나 건너뛰어도 괜찮아요','조건은 필요한 만큼 더 확인해요','체크리스트와 발급 안내로 연결','상담 요약을 복사 · PDF로 저장')
for($i=0;$i -lt 4;$i++) {
    $x=48+$i*381.5
    Round $g $x 178 359.5 776 26 '#ffffff' '#e3e9f1'
    Round $g ($x+20) 202 39 39 12 '#eaf2ff'
    Text $g ([string]($i+1)) ($x+20) 204 22 '#3182f6' $true 39 45 $true
    Text $g $titles[$i] ($x+69) 205 26 '#14243b' $true 284
    Text $g $intros[$i][0] ($x+21) 257 21 '#667c96' $false 320
    Text $g $intros[$i][1] ($x+21) 289 21 '#667c96' $false 320
    $screen=RoundPath ($x+20) 340 319.5 550 18
    $state=$g.Save(); $g.SetClip($screen)
    $img=[System.Drawing.Image]::FromFile((Join-Path (Join-Path $Repository 'assets/screens') $files[$i]))
    $height=319.5*$img.Height/$img.Width
    $g.DrawImage($img,[System.Drawing.RectangleF]::new(($x+20),340,319.5,$height)); $img.Dispose()
    $g.Restore($state)
    $pen=[System.Drawing.Pen]::new((Color '#dfe7f2'),1);$g.DrawPath($pen,$screen);$pen.Dispose();$screen.Dispose()
    Text $g $captions[$i] ($x+12) 910 20 '#2c4f78' $true 335 45 $true
}
Text $g '실제 브라우저 캡처 · 화면의 정책과 조건은 가상 체험 예시입니다.' 48 984 20 '#70849e' $false 1504 50 $true
$g.Dispose();$journey.Image.Save((Join-Path $destination 'journey.png'),[System.Drawing.Imaging.ImageFormat]::Png);$journey.Image.Dispose()
Write-Output 'Rendered cover.png (1600x680) and journey.png (1600x1050)'
