多边人工智能治理证据审议与异议保全台

运行验收：
python3 -m evidence_deliberation run --fixture fixtures/acceptance.json --database /tmp/evidence_deliberation.sqlite3 --output /tmp/evidence_deliberation-output

核验：
python3 -m evidence_deliberation verify --database /tmp/evidence_deliberation.sqlite3 --output /tmp/evidence_deliberation-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.evidence_signal.test_evidence_strength -v

构建检查：
python3 -m compileall -q evidence_deliberation tests
