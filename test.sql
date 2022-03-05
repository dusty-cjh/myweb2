ALTER TABLE shop_order ADD COLUMN extra_data TEXT NOT NULL;


select id from bankaccount_tab where
                                     bank_name_id not in (select bank_name_id from bank_name_tab)
                                  or bank_name not in (select bank_name from bank_name_tab)
                                  or region not in (select region from bank_region_tab)
                                  or branch_name not in (select branch_name from bank_branch_tab);

UPDATE bankaccount_tab as ba, bank_region_tab as br, bank_branch_tab as bb
SET ba.branch_name = bb.branch_name
WHERE
    ba.branch_name IN (
            select id from bankaccount_tab where status<>6 and branch_name not in (select branch_name from bank_branch_tab)
        )
AND
    ba.bank_name_id=bb.bank_name_id
AND
    ba.region=br.region_name
AND
    bb.bank_region_id=br.id
;


UPDATE bankaccount_tab AS ba, bank_name_tab AS bn
SET ba.bank_name =  bn.bank_name
WHERE
    ba.bank_name = ''
AND
    ba.bank_name_id=bn.id;
