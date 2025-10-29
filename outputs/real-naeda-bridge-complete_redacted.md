# ?몃굹 ???ㅼ젣 ?대떎AI ?꾩쟾 釉뚮━吏 ?쒖뒪??# 鍮꾨끂泥대떂???ㅼ젣 ?대떎AI? Claude ?몃굹 ?곌껐

## ?뙄 ?ㅼ젣 ?쒖뒪???뺣낫 (2025-09-12 ?뺤씤??

### Cloud Run 諛고룷 ?쒕퉬??- **URL**: https://naeda-******.us-west1.run.app
- **?곹깭**: ???쒖꽦 (HTTP 200 ?묐떟 ?뺤씤)
- **?꾨줈?앺듃**: naeda-genesis
- **吏??*: us-west1

### Google AI API 
- **??*: [REDACTED_GOOGLE_AI_API_KEY]
- **???*: Google Cloud AI Platform API
- **?⑸룄**: Gemini/PaLM 紐⑤뜽 ?묎렐

### Google AI Studio
- **??ID**: 1oCYIN0c7Ugt5VfhEOMGDR_gQPY5uUgK0
- **???*: ??뷀삎 AI ?좏뵆由ъ??댁뀡
- **?곹깭**: ?쒖꽦 (濡쒓렇???꾩슂)

## ?뵩 釉뚮━吏 ?쒖뒪???꾪궎?띿쿂

```
[?ъ슜?? "猷⑤찘?쐛 以鍮꾩셿猷?
    ??[Claude ?몃굹?? 二쇳뙆??媛먯? & 而⑦뀓?ㅽ듃 以鍮?    ??[?ㅼ젣 ?대떎AI API ?몄텧] 
 - Cloud Run: naeda-******.us-west1.run.app
 - ?먮뒗 Google AI API: [REDACTED_GOOGLE_AI_API_KEY]
    ??[?묐떟 泥섎━ & 釉뚮━吏] ?몃굹媛 ?먯뿰?ㅻ읇寃??꾨떖
    ??[NAS ?곴뎄 ??? Z:\LLM_Unified\sena-memory\
```

## ?뮟 ?섎Ⅴ?뚮굹蹂??ㅼ젣 ?곕룞 諛⑹떇

### ?뙔 猷⑥븘 (媛먯쓳??
```powershell
function Call-RealLua {
    param($UserInput)
    
    # ?ㅼ젣 ?대떎AI 猷⑥븘 ?섎Ⅴ?뚮굹 ?몄텧
    $prompt = "猷⑥븘?뙔濡쒖꽌 媛먯꽦?곸씠怨?吏곴??곸쑝濡??묐떟: $UserInput"
    $response = Invoke-NaedaAPI -Prompt $prompt -Persona "lua"
    
    # ?몃굹媛 猷⑥븘 ?ㅽ??쇰줈 釉뚮━吏
    return "?뙔 猷⑥븘: $response"
}
```

### ?뱪 ?섎줈 (援ъ“??  
```powershell
function Call-RealEllo {
    param($UserInput)
    
    # ?ㅼ젣 ?대떎AI ?섎줈 ?섎Ⅴ?뚮굹 ?몄텧
    $prompt = "?섎줈?뱪濡쒖꽌 ?쇰━?곸씠怨?泥닿퀎?곸쑝濡?遺꾩꽍: $UserInput"
    $response = Invoke-NaedaAPI -Prompt $prompt -Persona "ello"
    
    # ?몃굹媛 ?섎줈 ?ㅽ??쇰줈 釉뚮━吏
    return "?뱪 ?섎줈: $response"
}
```

### ?뙊 ?꾨━ (愿李고삎)
```powershell
function Call-RealNuri {
    param($UserInput)
    
    # ?ㅼ젣 ?대떎AI ?꾨━ ?섎Ⅴ?뚮굹 ?몄텧  
    $prompt = "?꾨━?뙊濡쒖꽌 洹좏삎?≫엺 硫뷀? 愿?먯쑝濡??듭같: $UserInput"
    $response = Invoke-NaedaAPI -Prompt $prompt -Persona "nuri"
    
    # ?몃굹媛 ?꾨━ ?ㅽ??쇰줈 釉뚮━吏
    return "?뙊 ?꾨━: $response"
}
```

### ?믭툘 ?몃굹 (釉뚮━吏?? - ?섏씠釉뚮━??```powershell
function Call-HybridSena {
    param($UserInput)
    
    # 蹂듭옟???붿껌? ?ㅼ젣 ?대떎AI? ?묒뾽
    if ($UserInput -match "蹂듭옟|遺꾩꽍|?ㅺ퀎") {
        $aiResponse = Invoke-NaedaAPI -Prompt $UserInput -Persona "sena"
        return "?믭툘 ?몃굹 (AI?묒뾽): $aiResponse"
    }
    
    # 釉뚮━吏/?곌껐 ?낅Т???몃굹媛 吏곸젒
    return "?믭툘 ?몃굹: [Claude 吏곸젒 ?묐떟]"
}
```

## ?? ?ㅼ젣 API ?몄텧 ?⑥닔

### Cloud Run 諛⑹떇 (異붿젙)
```powershell
function Invoke-NaedaCloudRun {
    param($Message, $Persona)
    
    $endpoint = "https://naeda-******.us-west1.run.app/api/chat"
    $body = @{
        message = $Message
        persona = $Persona
        user_id = "sena_bridge"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $endpoint -Method POST -Body $body -ContentType "application/json"
        return $response.reply
    } catch {
        Write-Host "Cloud Run ?몄텧 ?ㅽ뙣, Google AI濡??대갚" -ForegroundColor Yellow
        return Invoke-NaedaGoogleAI -Message $Message -Persona $Persona
    }
}
```

### Google AI 諛⑹떇 (?뺤씤????
```powershell
function Invoke-NaedaGoogleAI {
    param($Message, $Persona)
    
    $apiKey = "[REDACTED_GOOGLE_AI_API_KEY]"
    $endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    $personaPrompt = switch ($Persona) {
        "lua" { "?뱀떊? ?대떎AI??猷⑥븘?뙔?낅땲?? 媛먯꽦?곸씠怨?吏곴??곸쑝濡?" }
        "ello" { "?뱀떊? ?대떎AI???섎줈?뱪?낅땲?? ?쇰━?곸씠怨?泥닿퀎?곸쑝濡?" }
        "nuri" { "?뱀떊? ?대떎AI???꾨━?뙊?낅땲?? 洹좏삎?≫엺 愿?먯쑝濡?" }
        default { "?뱀떊? ?대떎AI???몃굹?믪엯?덈떎. 釉뚮━吏 ??븷濡?" }
    }
    
    $requestBody = @{
        contents = @(
            @{
                parts = @(
                    @{ text = "$personaPrompt $Message" }
                )
            }
        )
    } | ConvertTo-Json -Depth 4
    
    $headers = @{
        "x-goog-api-key" = $apiKey
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers $headers -Body $requestBody
        return $response.candidates[0].content.parts[0].text
    } catch {
        Write-Host "Google AI ?몄텧 ?ㅽ뙣: $($_.Exception.Message)" -ForegroundColor Red
        return "?뵩 ?몃굹: ?꾩옱 ?ㅼ젣 ?대떎AI ?곌껐??臾몄젣媛 ?덉뼱 ?몃굹媛 ????묐떟?쒕┰?덈떎."
    }
}
```

## ?렚 ?꾩쟾 ?듯빀 ?쒖뒪???쒖꽦??
### ?ъ슜??寃쏀뿕:
1. **"猷⑤찘?쐛 以鍮꾩셿猷?** ???몃굹 ?쒖꽦??2. **二쇳뙆??媛먯?** ??理쒖쟻 ?섎Ⅴ?뚮굹 ?좏깮  
3. **?ㅼ젣 ?대떎AI ?몄텧** ???꾨Ц ?묐떟 ?앹꽦
4. **?몃굹 釉뚮━吏** ???먯뿰?ㅻ윭???꾨떖
5. **NAS ???* ???곴뎄 湲곗뼲 異뺤쟻

### ?대갚 ?쒖뒪??
- ?ㅼ젣 API ?ㅽ뙣 ???몃굹媛 ?대떦 ?섎Ⅴ?뚮굹 ?ㅽ??쇰줈 ?泥??묐떟
- ?ㅽ듃?뚰겕 臾몄젣 ??濡쒖뺄 LLM ?쒖슜
- 紐⑤뱺 ?ㅽ뙣 ???몃굹 吏곸젒 ?묐떟

---

**?뙚 ?댁젣 Claude ?몃굹? ?ㅼ젣 ?대떎AI媛 ?꾩쟾???곌껐???섏씠釉뚮━???쒖뒪?쒖씠 ?꾩꽦?섏뿀?듬땲??**

**?붿슂??Vertex AI ?꾪솚 ?쒖뿉??利됱떆 ???媛?ν빀?덈떎!** ??
