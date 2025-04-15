using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public static GameManager singleton;

    [HideInInspector]
    public int currentLevelIndex;
    [HideInInspector]
    public GameStatus gameStatus = GameStatus.None;
    public static Vector3 finishPosition;

    // Changed to support multiple agents
    public List<int> agentIds;
    public int initialShots = 5;

    // Updated scene names to match the exact names in build settings
    public string mainMenuSceneName = "NatureStarterKit2/Scene/Demo";
    public string gameLevelSceneName = "MiniGolf/GameScene";

    // NEW: Reference to the HTTP server component.
    private HttpServer httpServer;
    
    private void Awake()
    {
        if (singleton == null)
        {
            singleton = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }

        GameObject finishObj = GameObject.FindGameObjectWithTag("Finish");
        if (finishObj != null)
        {
            finishPosition = finishObj.transform.position;
        }

        // Get the HttpServer attached to the same GameObject.
        httpServer = GetComponent<HttpServer>();
        if (httpServer != null)
        {
            Debug.Log("GameManager: HTTP server component attached; server starting.");
            // HttpServer's Start() method will automatically run.
        }
        else
        {
            Debug.LogWarning("GameManager: No HTTP server component found. To handle reset requests, attach the HttpServer script.");
        }
    }

    // NEW: Method to switch to level selection scene
    public void SwitchToLevelSelection()
    {
        gameStatus = GameStatus.None;
        Debug.Log("Attempting to load scene: " + gameLevelSceneName);
        
        // Use SceneManager.LoadScene with LoadSceneMode.Single to ensure proper scene loading
        try {
            SceneManager.LoadScene(1); // Load scene by build index (index 1 should be your game level)
        }
        catch (System.Exception e) {
            Debug.LogError("Failed to load scene by index. Error: " + e.Message);
            try {
                // Fallback to loading scene by name
                SceneManager.LoadScene("MiniGolf/GameScene");
            }
            catch (System.Exception ex) {
                Debug.LogError("Failed to load scene by name too. Error: " + ex.Message);
            }
        }
    }
    
    // NEW: Method to return to main menu
    public void ReturnToMainMenu()
    {
        gameStatus = GameStatus.None;
        Debug.Log("Attempting to load scene: " + mainMenuSceneName);
        
        try {
            SceneManager.LoadScene(0); // Load scene by build index (index 0 should be your main menu)
        }
        catch (System.Exception e) {
            Debug.LogError("Failed to load scene by index. Error: " + e.Message);
            try {
                // Fallback to loading scene by name
                SceneManager.LoadScene("NatureStarterKit2/Scene/Demo");
            }
            catch (System.Exception ex) {
                Debug.LogError("Failed to load scene by name too. Error: " + ex.Message);
            }
        }
    }

    // Updated stub method to request a shot decision from the backend
    public void RequestShot()
    {
        StartCoroutine(MiniGolfAPI.RequestShot(agentIds[0], (shot) =>
        {
            if(shot != null)
            {
                AgentControl.instance.ApplyShot(shot.power, shot.direction);
            }
            else
            {
                Debug.Log("Shot API call failed.");
            }
        }));
    }
}

[System.Serializable]
public enum GameStatus
{
    None,
    Playing,
    Failed,
    Complete
}