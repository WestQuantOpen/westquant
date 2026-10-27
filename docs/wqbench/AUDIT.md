# Revision av öppna datamotorn, 2026-10-27

Granskat: `generate.py`, `wqdf.py`, pyproject och README i WestQuantOpen/westquant. Inte granskat: privata WQT50M-koden eller 1.8M ursprungsposter.

- `_compile_qiskit` tar emot backend/noise_model men skickar varken Target/Backend/coupling map eller brusmodell vidare. Backendnamn i data kan därför inte ensamt tolkas som en faktisk hårdvarukonditionering.
- Fel fångas i hjälpfunktion och toppnivå; WQDFSample har inget compile_success/error/status-fält. Fel kan serialiseras med depth/size/two_qubit_gates=0 och förlorat felmeddelande.
- sample_id beror bara på framework och lokalt index; kollisioner mellan anrop.
- search_space dokumenteras men styr inte genereringslogiken.
- Pulser-adaptern returnerar compile_success=True och nollmått utan att visa faktisk kompilering.
- Det finns ingen före/efter-kretskoppling, explicit semantisk verifiering, targetvalidering eller root-baserad split i dessa moduler.
- Parquet-fallback byter format till JSONL utan ett tydligt fel till anroparen.

Detta belägger problem i den öppna implementationen. Det belägger inte att samma fel finns i WQT50M:s separata träningspipeline. 15-kretsuppgiften kommer från den bifogade planen; modellkortets fullständiga innehåll gick inte att hämta via den anslutna källan.

Implementation v0.1 lägger till en separat strikt kärna i stället för att tyst ändra det befintliga API:t. Legacygeneratorn ska inte användas för nya WQBench-publiceringslabels innan en uttrycklig migrering.

## Kontroll av planens nämnare

Den bifogade planens nominella fulla produkt 50000 kretsar ×6 backends ×12 actions ×5 mål är 18000000, inte 1800000. Det betyder inte att dataposter saknas: datan kan vara subsamplad, mål kan vara alternativa vyer och kombinationer kan vara otillåtna. Men faktiskt enumererade, försöka, lyckade och exporterade poster måste separeras och förklaras av ett manifest. Nya kärnan räknar varje faktisk kompilering en gång; mål kan senare härledas från råmåtten utan omkompilering.
