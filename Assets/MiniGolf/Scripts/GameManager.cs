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

    // // Updated stub method to request a shot decision from the backend
    // public void RequestShot()
    // {
    //     StartCoroutine(MiniGolfAPI.RequestShot(agentIds[0], (shot) =>
    //     {
    //         if(shot != null)
    //         {
    //             AgentControl.instance.ApplyShot(shot.power, shot.direction);
    //         }
    //         else
    //         {
    //             Debug.Log("Shot API call failed.");
    //         }
    //     }));
    // }
}

[System.Serializable]
public enum GameStatus
{
    None,
    Playing,
    Failed,
    Complete
}