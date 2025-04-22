using UnityEngine;

/// <summary>
/// Ensures an HttpServer instance is present in any scene
/// This script should be added to the Demo scene
/// </summary>
public class NetworkInitializer : MonoBehaviour
{
    // Singleton instance
    public static NetworkInitializer Instance { get; private set; }
    private GameObject httpServerObject;

    private void Awake()
    {
        // Implement singleton pattern
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            
            // Create HttpServer if none exists
            if (FindObjectOfType<HttpServer>() == null)
            {
                httpServerObject = new GameObject("HttpServerObject");
                httpServerObject.AddComponent<HttpServer>();
                DontDestroyOnLoad(httpServerObject);
                Debug.Log("NetworkInitializer: Created new HttpServer object");
            }
            else
            {
                Debug.Log("NetworkInitializer: HttpServer already exists");
            }
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void OnDestroy()
    {
        // Clean up if this is the instance being destroyed
        if (Instance == this)
        {
            Instance = null;
        }
    }
}