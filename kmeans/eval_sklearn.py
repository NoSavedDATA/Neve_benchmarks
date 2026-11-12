import numpy as np
import time
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def evaluate_accuracy(true_labels, pred_labels, K=6):
    cluster_to_label = np.zeros(K, dtype=int)
    
    for c_i in range(K):
        mask = (pred_labels == c_i)
        if np.any(mask):
            counts = np.bincount(true_labels[mask])
            cluster_to_label[c_i] = np.argmax(counts)
            
    mapped_labels = cluster_to_label[pred_labels]
    accuracy = np.mean(mapped_labels == true_labels)
    
    print(f"Correctly clustered: {np.sum(mapped_labels == true_labels)} / {len(true_labels)}")
    print(f"Accuracy: {accuracy * 100.0:.2f}%")
    return accuracy

if __name__ == "__main__":
    X_train = np.loadtxt("/root/Datasets/har/train/X_train.txt")
    y_train = np.loadtxt("/root/Datasets/har/train/y_train.txt", dtype=int) - 1
    
    X_test = np.loadtxt("/root/Datasets/har/test/X_test.txt")
    y_test = np.loadtxt("/root/Datasets/har/test/y_test.txt", dtype=int) - 1

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    st = time.time()
    kmeans = KMeans(n_clusters=6, n_init='auto')
    kmeans.fit(X_train_scaled)
    
    test_predictions = kmeans.predict(X_test_scaled)
    evaluate_accuracy(y_test, test_predictions)


    print(f"kmeans time: {time.time()-st}")
