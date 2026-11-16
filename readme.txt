多边人工智能治理证据审议与异议保全台

运行验收：
python3 -m evidence_deliberation run --fixture fixtures/acceptance.json --database /tmp/evidence_deliberation.sqlite3 --output /tmp/evidence_deliberation-output

核验：
python3 -m evidence_deliberation verify --database /tmp/evidence_deliberation.sqlite3 --output /tmp/evidence_deliberation-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.evidence_signal.test_evidence_strength -v
python3 -m unittest tests.dissent.test_objections tests.dissent.test_objection_flow -v

构建检查：
python3 -m compileall -q evidence_deliberation tests

异议评估决议审议（fixtures/objections.json）：
  每条异议通过 evidence_refs 指向原主张记录(target_record_id)与支持材料，并归入
  claim_id/topic/scope_condition 定义的主张链(chain_key)。评估给出三种状态：
    responded     已有不弱于异议权重的回应证据，不阻断发布
    disputed      异议有依据但仍未被充分回应，压住待发布决议
    insufficient  异议缺乏支持材料或材料权重过低(低于 0.35)，同样阻断发布
  发布摘要 summary.json 的 release_gate 与 release_status 反映上述状态；
  dissent.unresolved 可从发布摘要追溯到每条仍未解决的反驳及其证据。
python3 -m evidence_deliberation run --fixture fixtures/objections.json --database /tmp/dissent.sqlite3 --output /tmp/dissent-output

补充证据后仅重评受影响的主张链（fixtures/supplement.json）：
  更新记录或提交异议回应只会重评所在主张链；未受影响的链不会重新决策。
  已归档决议在 resolution_archives 中固化当时引用的记录版本、决策指纹与证据，
  新证据可入库为新版本，但不改变归档内容。
python3 -m evidence_deliberation supplement --fixture fixtures/supplement.json --database /tmp/dissent.sqlite3

导出产物：
  records.csv                  记录状态与每条记录的异议摘要状态(dissent_status)
  rules.csv                    规则证据
  objections.csv               异议→主张→支持材料/回应→评估状态与钉住的记录指纹
  summary.json                 发布闸门、异议三态计数、未解决反驳追溯、归档决议
  decisions.json               决策(含 blocking_objections 原因)
  objection-assessments.json   全部异议评估历史(仅追加)
  resolution-archives.json     归档决议固化的证据版本
  audit-events.json            哈希链审计事件
