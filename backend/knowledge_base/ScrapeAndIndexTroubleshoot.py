from TroubleshootInformation import TroubleshootInformation

from FaissIndexer import FaissIndexer

def scrape_and_index_troubleshoot():    
    repair_url = "https://www.partselect.com/Repair/"
    dishwasher_url = f"{repair_url}Dishwasher"
    refrigerator_url = f"{repair_url}Refrigerator"
    dishwasherTroubleshoot = TroubleshootInformation(dishwasher_url)
    print("Scraped Dishwasher Troubleshooting Data")
    faiss_dishwasher = FaissIndexer(dishwasherTroubleshoot.symptom_data)
    faiss_dishwasher.create_index()
    faiss_dishwasher.save_index("dishwasher_faiss_index.bin", "dishwasher_metadata.pkl")
    print("Finished Indexing Dishwasher Troubleshooting Data")
    refrigeratorTroubleshoot = TroubleshootInformation(refrigerator_url)
    faiss_refrigerator = FaissIndexer(refrigeratorTroubleshoot.symptom_data)
    faiss_refrigerator.create_index()
    faiss_refrigerator.save_index("refrigerator_faiss_index.bin", "refrigerator_metadata.pkl")
    print("Finished Indexing Dishwasher and Refrigerator Troubleshooting Data")
    print("Saved FAISS index and metadata for Dishwasher and Refrigerator")

if __name__ == "__main__":
    scrape_and_index_troubleshoot()
    print("Scraping and Indexing completed.")