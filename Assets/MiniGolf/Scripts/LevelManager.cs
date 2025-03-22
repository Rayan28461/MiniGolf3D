using UnityEngine;
using System.Collections.Generic;

public class LevelManager : MonoBehaviour
{
    public static LevelManager instance;

    public GameObject ballPrefab, agentPrefab;
    public Vector3 ballSpawnPos;
    public LevelData[] levelDatas;

    private int shotCount = 0;

    private void Awake()
    {
        if (instance == null)
            instance = this;
        else
            Destroy(gameObject);
    }

    public void SpawnLevel(int levelIndex)
    {
        
        // Spawn the level prefab.
        Instantiate(levelDatas[levelIndex].levelPrefab, Vector3.zero, Quaternion.identity);
        shotCount = levelDatas[levelIndex].shotCount;
        UIManager.instance.ShotText.text = shotCount.ToString();

        // Instantiate the ball and set the camera target.
        GameObject ball = Instantiate(ballPrefab, ballSpawnPos, Quaternion.identity);
        CameraFollow.instance.SetTarget(ball);

        List<GameObject> agents = new List<GameObject>(); // Store spawned agents

        for (int i = 0; i < 10; i++)
        {
            GameObject agent = Instantiate(agentPrefab, ballSpawnPos, Quaternion.identity);

            // Ignore collision with the ball
            Physics.IgnoreCollision(agent.GetComponent<Collider>(), ball.GetComponent<Collider>());

            // Ignore collision with other agents
            foreach (GameObject otherAgent in agents)
            {
                Physics.IgnoreCollision(agent.GetComponent<Collider>(), otherAgent.GetComponent<Collider>());
            }

            agents.Add(agent); // Store this agent for future ignores

            StartCoroutine(MiniGolfAPI.InitAgent(i, GameManager.singleton.initialShots, (response) =>
            {
                Debug.Log("Init API response for agent " + i + ": " + response);
            }));
        }


        // GameObject agent = Instantiate(agentPrefab, ballSpawnPos, Quaternion.identity);
        // Physics.IgnoreCollision(agent.GetComponent<Collider>(), ball.GetComponent<Collider>());

        GameManager.singleton.gameStatus = GameStatus.Playing;

        // For each agent, send an init call
        // foreach (int id in GameManager.singleton.agentIds)
        // {
        //     StartCoroutine(MiniGolfAPI.InitAgent(id, GameManager.singleton.initialShots, (response) =>
        //     {
        //         Debug.Log("Init API response for agent " + id + ": " + response);
        //     }));
        // }
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