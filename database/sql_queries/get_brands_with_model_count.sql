SELECT
    b.brand_id,
    b.brand_name AS "Бренд",
    COUNT(cm.model_id) AS "Кількість моделей"
FROM
    product_metadata.brands AS b
LEFT JOIN
    conditioners.conditioner_models AS cm
ON
    b.brand_id = cm.brand_id
GROUP BY
    b.brand_id,
    b.brand_name
HAVING
    COUNT(cm.model_id) > 0
ORDER BY
    b.brand_name;
