# DataTable Schema
### Schema by Demand

***
 - Model Name : event.event
 - Inhert (Delegation) Model : event.event
 - Description : 研究 event 結構做 需求交換系統 (資料結構為 TPH)

| Name                | Data Type                       | Attribute         | Comment    |
| ---                 | ---                             | ---               | ---        |
| mode                | Selection                       | +demand           | 主題分類   |

***
 - Model Name : event.demand
 - Inhert (Delegation) Model : event.event
 - Description : 擴充給需求交換系統所用 (資料結構為 TPT)
 - Comment : 主題 + 開始時間

| Name                | Data Type                       | Attribute         | Comment         |
| ---                 | ---                             | ---               | ---             |
| event_id            | Many2one(event.event)           |                   | 關聯主題(event) |
| demand_type         | Selection                       | taker/giver       | 提/供 方        |
| state               | Selection                       | draft/open/cancel | 審核狀態        |
| minion_ids          | One2many(evnet.demand.schedule) | master_id         | 時間表樣板      |

***
 - Model Name : event.event.ticket
 - Inhert (Delegation) Model : event.event.ticket
 - Description : 擴充票種的欄位
 - Comment : 定價
 
| Name              | Data Type      | Attribute | Comment         |
| ---               | ---            | ---       | ---             |
| pricing_method    | Selection      |           | 計價方式        |

***
 - Model Name : event.registration
 - Inhert (Delegation) Model : event.registration
 - Description : 擴充 Giver 和 Taker 相關資訊
 - Comment : 與會者的訂單資訊
 
| Name              | Data Type                     | Attribute | Comment         |
| ---               | ---                           | ---       | ---             |
| demand_po_id      | Many2one(purchase.order)      | set null  | Taker的訂單     |
| demand_po_line_id | Many2one(purchase.order.line) | set null  | Taker的訂單明細 |
| demand_so_id      | Many2one(sale.order)          | set null  | Giver的訂單     |
| demand_so_line_id | Many2one(sale.order.line)     | set null  | Giver的訂單明細 |
