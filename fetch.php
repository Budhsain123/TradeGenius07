<?php

$sourceApi = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json";
$file = "data.json";

/* ---- cURL request ---- */
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $sourceApi);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 15);

// IMPORTANT HEADERS
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept: application/json",
    "Referer: https://draw.ar-lottery01.com/"
]);

$response = curl_exec($ch);

if ($response === false) {
    curl_close($ch);
    exit("CURL ERROR");
}

$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200) {
    exit("API BLOCKED : HTTP $httpCode");
}

/* ---- JSON decode ---- */
$res = json_decode($response, true);
$list = $res['data']['list'] ?? [];

/* ---- load old data safely ---- */
$stored = [];
if (file_exists($file)) {
    $old = json_decode(file_get_contents($file), true);
    if (is_array($old)) {
        $stored = $old;
    }
}

/* ---- issueNumber map ---- */
$map = [];
foreach ($stored as $row) {
    if (isset($row['issueNumber'])) {
        $map[$row['issueNumber']] = true;
    }
}

/* ---- save only new issueNumber ---- */
foreach ($list as $item) {
    if (!isset($item['issueNumber'], $item['number'])) continue;

    if (isset($map[$item['issueNumber']])) continue;

    $stored[] = [
        "issueNumber" => $item['issueNumber'],
        "number" => $item['number'],
        "time" => time()
    ];

    $map[$item['issueNumber']] = true;
}

/* ---- limit 10,000 ---- */
if (count($stored) > 10000) {
    $stored = array_slice($stored, -10000);
}

file_put_contents($file, json_encode($stored));

echo "OK";