def test_upload_csv(client, sample_csv_bytes):
    response = client.post("/upload",files={ "file": ( "sample_data.csv", sample_csv_bytes, "text/csv")})
    info = response.json()
    assert response.status_code == 200 
    assert info["rows"] == 6
    assert info["columns"] == 2
    assert info["id"] > 0 and isinstance(info["id"],int)

def test_process_and_retrieve(client, uploaded_dataset_id, processing_body):
    response = client.post(f"/datasets/{uploaded_dataset_id}/process", json=processing_body)
    info = response.json()
    assert response.status_code == 200
    assert info["validation_rows_removed"] == 1
    assert info["cleaning_report"]['rows_before'] == 5 and info["cleaning_report"]['rows_after'] == 3


    response_2 = client.get(f"/datasets/{uploaded_dataset_id}")
    info_2 = response_2.json()
    student_ids = [row["student_id"] for row in info_2["data"]]
    student_scores = [row["score"] for row in info_2["data"]]
    assert response_2.status_code == 200
    assert info_2["total_rows"] == 3
    assert student_ids == [1,2,5] and student_scores == [80,90,85]

def test_retrieve_missing_dataset(client):
    response = client.get("/datasets/9999")
    assert response.status_code == 404