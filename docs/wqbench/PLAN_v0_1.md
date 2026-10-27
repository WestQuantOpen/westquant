# WQBench foundation: plan före implementation, 2026-10-27

## Problem och formalisering

För varje grundkrets C, explicit Target T, kompilatorkonfiguration a och seed s ska en verklig kompilering ge råmått m samt separat verifierings- och målvaliditetsstatus. Varje försök, även fel, ingår i nämnaren. Olika målvikter är analysvyer över samma kompilering och ska inte skapa påstått oberoende experiment. Familj/grundproblem, inte post, är analysenhet.

Befintlig öppen motor `src/westquant/generate.py` granskas. Den skiljer sig från den privata WQT50M-pipelinen, som inte har granskats. Uppgifterna om 1.8M poster och 15 testkretsar i användarens bifogade plan behandlas som rapporterade, inte oberoende verifierade. Inga slutsatser om privatdatasetets fel dras från den öppna koden.

H0 korrekthet: små unitära kretsar, efter full layoutkorrigering, ska vara ekvivalenta upp till global fas till tolerans 1e-9. För större/dynamiska kretsar ska resultatet vara UNKNOWN, aldrig obestyrkt EXACT. H1 system: körning med resume ska ge exakt samma uppgifts-ID:n och inte räkna cacheträffar som nya observationer. H2 läckage: alla härledda varianter av ett root_id ska få samma split. Dessa är programvarukrav, inte hypoteser om att WQT vinner.

Närliggande primärkällor, kontrollerade 2026-10-27: MQT Bench dokumentation (kretsgeneratorer, stödda algoritmer); MQT Predictor dokumentation (device selection, device-specific compilation). https://mqt.readthedocs.io/projects/bench/en/latest/ och https://mqt.readthedocs.io/projects/predictor/en/latest/. Ingen nyhetsclaim om att ett gemensamt benchmark saknas görs utan bredare litteraturrevision. NeurIPS 2027-regler eller deadline är inte verifierade och styr inte denna implementation.

## Lösning

En separat modul `westquant.wqbench` i existerande umbrella-repo; gammal API behålls. Normaliserad SQLite-lagring med circuits, backends och runs; råa JSONL-exporter. TargetSpec bygger Qiskit Target med dokumenterade syntetiska gatefel/durationer. Denna första etapp omfattar optimization_level 0–3, INTE de tolv privata actions eller multistegspass. Inga QPU-jobb eller modellträningar.

SHA256 av ett versionssatt, exakt instruktionsdokument ger content_id. Det är en representationshash, inte en semantisk kanonisering. Ursprungligt root_id krävs; det grupperar gauger, parametrar och permutationer via proveniens. En härledd template-hash räcker inte som bevis att orelaterade inputs är oberoende. Datasetexporten bevarar källkod och kompilerad krets, seed, config, miljö och gitrevision. Backendproveniens måste vara synthetic eller measured med källa; nu implementerade mål är synthetic.

Råmått: djup, storlek, grindhistogram, tvåqubitsgrindar, gate_time_sum_seconds och independent_gate_success_proxy. Proxy är en oberoende produktmodell, inte uppmätt framgång eller kvanttillståndsfidelitet. Summan av gate-tider är inte schemalagd kritisk väglängd. Olika kommando-/konfigurationshashar ger separata run-id:n. Saknade värden är null, inte noll.

## Prövning och begränsningar

Första smoke-workload: 3 familjer (GHZ, QAOA, slump), 2 storlekar (3,4), 2 instansseeds =12 källkretsar inom 10 ursprungsgrupper (GHZ-vinkelvarianter delar root); 2 topologier (line,ring), 4 nivåer, 2 transpilerseeds =192 kompileringar. Därefter samma körning med resume: 0 nya kompileringar. Detta är en pipelinekontroll, inte ett oberoende modellbenchmark och ingen prestandastudie. Tak: 5 minuter lokal CPU för smoke, ingen molnkostnad.

Meningsfulla tester: target routing, layoutkorrigerad operator-ekvivalens, skadad krets upptäcks, UNKNOWN vid för stor verifieringsuppgift, felposter utan fabricerade mått, olika inputs får olika ID:n, samma root håller ihop splits, targetändring invalidaterar cache, resume och nollnämnare i regret.

Full matris S0–S5 och T1–T6 i användarens plan är roadmap. Statistik för modelljämförelser ska låsas senare med krets-/blockbootstrap och variansbaserad budget, inte behandla 192 rader som 192 problem. S2 kräver eget backendholdout-manifest, inte att blanda dess axel med S0:s root-split. En normalized-regret-denominator utan orakelvinst är odefinierad och redovisas separat. Beam search är en heuristisk referens, inget exakt flerstegsorakel.

Semantiska gates: failed ekuivalens utesluter raden från legitima åtgärdslabels, UNKNOWN förblir UNKNOWN; fysisk koppling och gate-support valideras separat. GHZ kräver kompletterande basmätningar för koherensclaims. Ruby analog Pulser får ingen påhittad universell gateadapter. Befintliga gauge-hårdvarudata är ett separat experiment och ersätter inte benchmarkens frysta hårdvaruset.

Beslut: implementera och verifiera denna grund nu. Nästa etapp är revision/import av existerande rådata, Parquet/schemaexport och större oberoende kretsmanifest; först därefter full datafabrik och modellbenchmark. Befintlig DATA_POLICY kräver uttryckligt val av vad som ska bli öppet: nuvarande privata träningsdata publiceras inte genom denna uppgift.

Preciserat före slutlig smoke: GHZ:s två vinkelvarianter per storlek räknas som två källkretsar men EN ursprungsgrupp. Antalet kompileringar är fortfarande 192, men oberoende gruppnämnare är 10, inte 12. Detta är ett avsiktligt test av proveniensgrupperingen.
