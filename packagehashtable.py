class ChainingHashTable:
    def __init__(self, initial_capacity=40):
        # Set up the table with empty buckets
        self.table = [[] for _ in range(initial_capacity)]

    def insert(self, key, item):
        # Find which bucket this key should go into
        bucket_index = hash(key) % len(self.table)
        bucket = self.table[bucket_index]

        # Check if key already exists—if so, update it
        for kv in bucket:
            if kv[0] == key:
                kv[1] = item
                return True

        # Otherwise, add a new key-value pair
        bucket.append([key, item])
        return True

    def search(self, key):
        # Look in the appropriate bucket for the key
        bucket_index = hash(key) % len(self.table)
        bucket = self.table[bucket_index]

        for kv in bucket:
            if kv[0] == key:
                return kv[1]
        return None

    def remove(self, key):
        # Try to find and remove the key from the correct bucket
        bucket_index = hash(key) % len(self.table)
        bucket = self.table[bucket_index]

        for i, kv in enumerate(bucket):
            if kv[0] == key:
                del bucket[i]
                return True
        return False
