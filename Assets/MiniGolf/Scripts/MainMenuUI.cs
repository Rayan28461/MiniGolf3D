using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class MainMenuUI : MonoBehaviour
{
    [SerializeField] private Button playButton;
    [SerializeField] private Button quitButton;
    [SerializeField] private GameObject mainMenuPanel;

    [SerializeField] private string levelSelectionSceneName = "MiniGolf/GameScene";
    [SerializeField] private int levelSelectionSceneIndex = 1; // Use scene index instead of name

    private void Start()
    {
        // Add button listeners
        if (playButton != null)
        {
            playButton.onClick.AddListener(PlayGame);
        }
        
        if (quitButton != null)
        {
            quitButton.onClick.AddListener(QuitGame);
        }
        
        // Make sure the main menu panel is active
        if (mainMenuPanel != null)
        {
            mainMenuPanel.SetActive(true);
        }

        // Ensure GameManager is present
        if (GameManager.singleton == null)
        {
            Debug.LogWarning("GameManager not found. Creating a temporary one.");
            GameObject gameManagerObj = new GameObject("GameManager");
            GameManager gameManager = gameManagerObj.AddComponent<GameManager>();
            gameManager.gameLevelSceneName = levelSelectionSceneName;
        }
    }

    public void PlayGame()
    {
        Debug.Log("Play button clicked - attempting to load game scene");
        
        // If GameManager exists, use it, otherwise load the scene directly by index
        if (GameManager.singleton != null)
        {
            GameManager.singleton.SwitchToLevelSelection();
        }
        else
        {
            try {
                SceneManager.LoadScene(levelSelectionSceneIndex);
                Debug.Log("Loading scene by index: " + levelSelectionSceneIndex);
            }
            catch (System.Exception e) {
                Debug.LogError("Failed to load scene by index: " + e.Message);
                try {
                    SceneManager.LoadScene(levelSelectionSceneName);
                    Debug.Log("Loading scene by name: " + levelSelectionSceneName);
                }
                catch (System.Exception ex) {
                    Debug.LogError("Failed to load scene by name too: " + ex.Message);
                }
            }
        }
    }

    public void QuitGame()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}