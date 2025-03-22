using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class GameManager : MonoBehaviour
{
    public static GameManager singleton;

    [HideInInspector]
    public int currentLevelIndex;
    [HideInInspector]
    public GameStatus gameStatus = GameStatus.None;

    // Changed to support multiple agents
    public List<int> agentIds = new List<int> { 1, 2, 3, 4, 5, 6 };
    public int initialShots = 5;
    
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

        // Debug.Log("Agent IDs on Awake: " + string.Join(", ", agentIds));
    }

    // Stub method to send ball data.
    public void SendBallData(Vector3 position, string tag)
    {
        Debug.Log("Ball data sent: " + position + " with tag: " + tag);
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