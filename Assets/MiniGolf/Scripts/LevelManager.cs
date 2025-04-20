using UnityEngine;
using System.Collections.Generic;
using UnityEngine.SceneManagement;

public class LevelManager : MonoBehaviour
{
    public static LevelManager instance;

    public GameObject ballPrefab, agentPrefab;
    public Vector3 ballSpawnPos;
    public LevelData[] levelDatas;
    public int numberOfAgents;

    private int shotCount = 5;

    private void Awake()
    {
        Debug.Log("[DEBUG] from LevelManager: Level Awake()");
        if (instance == null)
            instance = this;
        else
            Destroy(gameObject);
    }

    public void ResetLevel()
    {
        // Hours wasted on these 2 lines : 5h
        GameManager.singleton.gameStatus = GameStatus.Failed;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }
    
    public void SpawnLevel(int levelIndex)
    {
        // Send the agent count to the backend.
        // StartCoroutine(SendAgentCount());

        // Spawn the level prefab.
        Instantiate(levelDatas[levelIndex].levelPrefab, Vector3.zero, levelDatas[levelIndex].levelPrefab.transform.rotation);
        shotCount = levelDatas[levelIndex].shotCount;
        UIManager.instance.ShotText.text = shotCount.ToString();

        // Instantiate the ball and set the camera target.
        // GameObject ball = Instantiate(ballPrefab, ballSpawnPos, Quaternion.identity);
        // CameraFollow.instance.SetTarget(ball);

        List<GameObject> agents = new List<GameObject>(); // Store spawned agents

        for (int i = 0; i < numberOfAgents; i++)
        {
            // Use agent position from levelDatas if available, otherwise fallback to ballSpawnPos.
            Vector3 spawnPos = (levelDatas[levelIndex].agentPositions != null && 
                                i < levelDatas[levelIndex].agentPositions.Length) 
                                 ? levelDatas[levelIndex].agentPositions[i] 
                                 : ballSpawnPos;
            GameObject agent = Instantiate(agentPrefab, spawnPos, Quaternion.identity);

            // Ignore collision with the ball
            // Physics.IgnoreCollision(agent.GetComponent<Collider>(), ball.GetComponent<Collider>());
            // Ignore collision with other agents
            foreach (GameObject otherAgent in agents)
            {
                Physics.IgnoreCollision(agent.GetComponent<Collider>(), otherAgent.GetComponent<Collider>());
            }
            
            agents.Add(agent); // Store agent

            // Set current id = number of spawned agents before + 1.
            int currentId = i + 1;
            agent.GetComponent<AgentControl>().id = currentId;
            
            // Chain API call: After initialization, send environment data and request shot in one call.
            // StartCoroutine(MiniGolfAPI.InitAgent(currentId, GameManager.singleton.initialShots, (initResponse) =>
            // {
            //     // Vector3 ballPos = ball.transform.position;
            //     Vector3 holePos = GameManager.finishPosition;
            //     // UPDATED: Use an empty SerializedWallData array instead of a Vector3[].
            //     AgentControl.WallData[] walls = AgentControl.CollectNearbyWallPointsUsingRaycasts();
            //     StartCoroutine(MiniGolfAPI.RequestShotWithEnvironment(currentId, spawnPos, holePos, walls, (shot) =>
            //     {
            //         if (shot != null)
            //         {
            //             agent.GetComponent<AgentControl>().ApplyShot(shot.power, shot.direction);
            //         }
            //         else
            //         {
            //             Debug.Log("Shot API call failed for agent " + currentId);
            //         }
            //     }));
            // }));
        }

        GameManager.singleton.gameStatus = GameStatus.Playing;
    }

    // Coroutine to send agent count to backend
    System.Collections.IEnumerator SendAgentCount()
    {
        string url = $"{MiniGolfAPI.BaseUrl}/set_agent_count?count={numberOfAgents}";
        using (UnityEngine.Networking.UnityWebRequest www = UnityEngine.Networking.UnityWebRequest.Get(url))
        {
            yield return www.SendWebRequest();
            
            if (www.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                Debug.Log("Agent count sent successfully: " + numberOfAgents);
            }
            else
            {
                Debug.LogError("Failed to send agent count: " + www.error);
            }
        }
    }

    public void ShotTaken()
    {
        if (shotCount > 0)
        {
            shotCount--;
            UIManager.instance.ShotText.text = shotCount.ToString();

            if (shotCount <= 0)
            {
                LevelFailed();
            }
        }
    }

    public void LevelFailed()
    {
        if (GameManager.singleton.gameStatus == GameStatus.Playing)
        {
            GameManager.singleton.gameStatus = GameStatus.Failed;
            UIManager.instance.GameResult();
        }
    }

    public void LevelComplete()
    {
        if (GameManager.singleton.gameStatus == GameStatus.Playing)
        {
            if (GameManager.singleton.currentLevelIndex < levelDatas.Length)
            {
                GameManager.singleton.currentLevelIndex++;
            }
            else
            {
                GameManager.singleton.currentLevelIndex = 0;
            }

            GameManager.singleton.gameStatus = GameStatus.Complete;
            UIManager.instance.GameResult();
        }
    }
}